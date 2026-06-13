import { useEffect, useRef, useState, useCallback } from "react";
import { ServerMessage } from "../types";

interface WebSocketHookOptions {
  url?: string;
  onTranscript?: (text: string, role: "user" | "assistant") => void;
  onAudioResponse?: (data: string, format: string) => void;
  onLatency?: (metrics: any) => void;
  onStatusChange?: (state: string) => void;
  onError?: (message: string) => void;
}

export function useWebSocket(options: WebSocketHookOptions = {}) {
  const {
    url = "ws://localhost:8000/ws/voice",
    onTranscript,
    onAudioResponse,
    onLatency,
    onStatusChange,
    onError,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 3;

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log("WebSocket connected");
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        onStatusChange?.("idle");
      };

      ws.onmessage = (event) => {
        try {
          const message: ServerMessage = JSON.parse(event.data);

          switch (message.type) {
            case "session_ready":
              setConversationId(message.conversation_id);
              console.log(`Session ready: ${message.conversation_id}`);
              break;

            case "transcript":
              onTranscript?.(message.text, message.role);
              break;

            case "audio_response":
              onAudioResponse?.(message.data, message.format);
              break;

            case "latency":
              onLatency?.(message);
              break;

            case "status":
              onStatusChange?.(message.state);
              break;

            case "error":
              console.error(`Server error: ${message.message}`);
              onError?.(message.message);
              break;
          }
        } catch (err) {
          console.error("Failed to parse server message:", err);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        onError?.("Connection error");
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected");
        setIsConnected(false);
        wsRef.current = null;

        // Attempt reconnection
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 5000);
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})...`);
          setTimeout(connect, delay);
        } else {
          onError?.("Failed to reconnect after 3 attempts");
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error("Failed to connect:", err);
      onError?.("Failed to connect");
    }
  }, [url, onTranscript, onAudioResponse, onLatency, onStatusChange, onError]);

  // Disconnect
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setConversationId(null);
  }, []);

  // Send audio chunk
  const sendAudioChunk = useCallback((base64: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "audio_chunk",
          data: base64,
        })
      );
    }
  }, []);

  // Start session
  const sendStartSession = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "start_session",
          conversation_id: conversationId || undefined,
        })
      );
    }
  }, [conversationId]);

  // End session
  const sendEndSession = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "end_session",
        })
      );
    }
    disconnect();
  }, [disconnect]);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, []);

  return {
    isConnected,
    conversationId,
    connect,
    disconnect,
    sendAudioChunk,
    sendStartSession,
    sendEndSession,
  };
}
