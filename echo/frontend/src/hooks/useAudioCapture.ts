import { useEffect, useState, useRef, useCallback } from "react";
import { arrayBufferToBase64, chunkAudioBuffer } from "../utils/audioUtils";

interface UseAudioCaptureOptions {
  sampleRate?: number;
  chunkDurationMs?: number;
  onChunk?: (base64: string) => void;
  onError?: (error: string) => void;
}

export function useAudioCapture(options: UseAudioCaptureOptions = {}) {
  const {
    sampleRate = 16000,
    chunkDurationMs = 30,
    onChunk,
    onError,
  } = options;

  const [isCapturing, setIsCapturing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const bufferRef = useRef<Float32Array>(new Float32Array());

  const start = useCallback(async () => {
    try {
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: { ideal: sampleRate },
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      // Create audio context
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = audioContext;
      streamRef.current = stream;

      // Create source from microphone
      const source = audioContext.createMediaStreamSource(stream);

      // Create script processor node (30ms chunks)
      const bufferSize = Math.floor((chunkDurationMs * sampleRate) / 1000);
      const processor = audioContext.createScriptProcessor(bufferSize, 1, 1);
      processorRef.current = processor;

      // Process audio chunks
      processor.onaudioprocess = (event) => {
        const inputData = event.inputBuffer.getChannelData(0);
        const pcmData = new Int16Array(inputData.length);

        // Convert float32 to int16
        for (let i = 0; i < inputData.length; i++) {
          let s = Math.max(-1, Math.min(1, inputData[i]));
          pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
        }

        // Convert to base64 and send
        const base64 = arrayBufferToBase64(pcmData.buffer);
        onChunk?.(base64);
      };

      // Connect nodes
      source.connect(processor);
      processor.connect(audioContext.destination);

      setIsCapturing(true);
      setError(null);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Microphone access denied";
      setError(errorMsg);
      onError?.(errorMsg);
    }
  }, [sampleRate, chunkDurationMs, onChunk, onError]);

  const stop = useCallback(() => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    setIsCapturing(false);
    bufferRef.current = new Float32Array();
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return {
    isCapturing,
    error,
    start,
    stop,
  };
}
