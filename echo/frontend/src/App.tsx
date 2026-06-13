import { useState, useCallback, useEffect } from "react";
import { useWebSocket } from "./hooks/useWebSocket";
import { useAudioCapture } from "./hooks/useAudioCapture";
import { useAudioPlayback } from "./hooks/useAudioPlayback";
import { StatusBar } from "./components/StatusBar";
import { VoiceOrb } from "./components/VoiceOrb";
import { Transcript } from "./components/Transcript";
import { LatencyBadge } from "./components/LatencyBadge";
import { AgentState, TranscriptEntry, LatencyMetrics } from "./types";
import "./App.css";

function App() {
  const [agentState, setAgentState] = useState<AgentState>("idle");
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [latency, setLatency] = useState<LatencyMetrics | null>(null);
  const [isTalking, setIsTalking] = useState(false);

  // WebSocket hook
  const {
    isConnected,
    sendAudioChunk,
    sendStartSession,
    sendEndSession,
  } = useWebSocket({
    onTranscript: (text, role) => {
      setTranscript((prev) => [
        ...prev,
        {
          id: `${Date.now()}-${Math.random()}`,
          role,
          text,
          timestamp: new Date(),
        },
      ]);
    },
    onAudioResponse: (data, format) => {
      playAudio(data);
    },
    onLatency: (metrics) => {
      setLatency(metrics);
    },
    onStatusChange: (state) => {
      setAgentState(state as AgentState);
    },
    onError: (message) => {
      console.error("Error:", message);
      setAgentState("error");
    },
  });

  // Audio capture hook
  const { isCapturing, start: startCapture, stop: stopCapture } = useAudioCapture({
    onChunk: (base64) => {
      if (isConnected) {
        sendAudioChunk(base64);
      }
    },
  });

  // Audio playback hook
  const { isPlaying, playAudio } = useAudioPlayback();

  // Start talking button
  const handleStartTalking = useCallback(async () => {
    if (!isConnected) {
      setAgentState("error");
      return;
    }

    setIsTalking(true);
    sendStartSession();

    try {
      await startCapture();
    } catch (err) {
      console.error("Failed to start microphone:", err);
      setAgentState("error");
      setIsTalking(false);
    }
  }, [isConnected, sendStartSession, startCapture]);

  // Stop talking button
  const handleStopTalking = useCallback(() => {
    stopCapture();
    setIsTalking(false);
  }, [stopCapture]);

  // End conversation button
  const handleEndConversation = useCallback(() => {
    stopCapture();
    sendEndSession();
    setIsTalking(false);
  }, [stopCapture, sendEndSession]);

  // Clear transcript button
  const handleClearTranscript = useCallback(() => {
    setTranscript([]);
  }, []);

  // Show permission denied state
  if (!navigator.mediaDevices?.getUserMedia) {
    return (
      <div className="app">
        <StatusBar isConnected={false} state="error" />
        <div className="app-error">
          <h1>Microphone Not Available</h1>
          <p>Your browser doesn't support microphone access.</p>
          <p>Please use a modern browser (Chrome, Firefox, Safari, Edge) with HTTPS.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <StatusBar isConnected={isConnected} state={agentState} />

      <div className="app-main">
        <div className="app-orb-section">
          <VoiceOrb state={agentState} />

          <div className="app-controls">
            {!isTalking ? (
              <button
                className="btn btn-primary"
                onClick={handleStartTalking}
                disabled={!isConnected || isPlaying}
              >
                {isConnected ? "Start Talking" : "Connecting..."}
              </button>
            ) : (
              <button
                className="btn btn-secondary"
                onClick={handleStopTalking}
              >
                Stop Talking
              </button>
            )}

            {transcript.length > 0 && (
              <>
                <button
                  className="btn btn-outline"
                  onClick={handleClearTranscript}
                  disabled={isTalking}
                >
                  Clear Transcript
                </button>

                <button
                  className="btn btn-outline"
                  onClick={handleEndConversation}
                  disabled={isTalking}
                >
                  End Conversation
                </button>
              </>
            )}
          </div>
        </div>

        <Transcript entries={transcript} />
      </div>

      <LatencyBadge metrics={latency} />
    </div>
  );
}

export default App;
