import { useRef, useState, useCallback } from "react";
import { base64ToAudioBuffer } from "../utils/audioUtils";

interface UseAudioPlaybackOptions {
  onPlaybackEnd?: () => void;
  onError?: (error: string) => void;
}

export function useAudioPlayback(options: UseAudioPlaybackOptions = {}) {
  const { onPlaybackEnd, onError } = options;

  const [isPlaying, setIsPlaying] = useState(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<AudioBufferSourceNode | null>(null);

  const playAudio = useCallback(
    async (base64Mp3: string): Promise<void> => {
      try {
        // Create or get audio context
        if (!audioContextRef.current) {
          audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
        }

        const audioContext = audioContextRef.current;

        // Decode audio
        const audioBuffer = await base64ToAudioBuffer(base64Mp3, audioContext);

        // Create source
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        sourceRef.current = source;

        // Handle playback end
        source.onended = () => {
          setIsPlaying(false);
          onPlaybackEnd?.();
        };

        // Connect and play
        source.connect(audioContext.destination);
        source.start();
        setIsPlaying(true);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Playback error";
        onError?.(errorMsg);
        setIsPlaying(false);
      }
    },
    [onPlaybackEnd, onError]
  );

  const stop = useCallback(() => {
    if (sourceRef.current) {
      try {
        sourceRef.current.stop();
      } catch {
        // Already stopped
      }
      sourceRef.current = null;
    }
    setIsPlaying(false);
  }, []);

  return {
    isPlaying,
    playAudio,
    stop,
  };
}
