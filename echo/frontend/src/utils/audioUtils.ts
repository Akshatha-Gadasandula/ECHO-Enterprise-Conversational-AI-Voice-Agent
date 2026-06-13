/**
 * Audio utility functions for encoding/decoding and chunking.
 */

/**
 * Convert Web Audio API AudioBuffer to mono 16-bit PCM at 16kHz.
 * @param audioBuffer - AudioBuffer from Web Audio API
 * @param targetSampleRate - Target sample rate (default 16000)
 * @returns ArrayBuffer containing mono PCM data
 */
export function convertToMonoPCM(
  audioBuffer: AudioBuffer,
  targetSampleRate: number = 16000
): ArrayBuffer {
  const offlineContext = new OfflineAudioContext(
    1, // mono
    Math.ceil((audioBuffer.duration * targetSampleRate) / audioBuffer.sampleRate),
    targetSampleRate
  );

  const source = offlineContext.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(offlineContext.destination);
  source.start();

  const renderedBuffer = offlineContext.startRendering() as Promise<AudioBuffer>;

  return renderedBuffer.then((buffer) => {
    const pcmData = buffer.getChannelData(0); // Get mono channel
    const int16Array = new Int16Array(pcmData.length);

    // Convert float32 to int16
    for (let i = 0; i < pcmData.length; i++) {
      let s = Math.max(-1, Math.min(1, pcmData[i])); // Clamp
      int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7fff; // Convert to int16
    }

    return int16Array.buffer;
  }) as any;
}

/**
 * Split a PCM ArrayBuffer into fixed-size chunks.
 * @param buffer - PCM ArrayBuffer
 * @param chunkSizeMs - Chunk duration in milliseconds (default 30ms)
 * @param sampleRate - Sample rate (default 16000)
 * @returns Array of ArrayBuffers, each representing a chunk
 */
export function chunkAudioBuffer(
  buffer: ArrayBuffer,
  chunkSizeMs: number = 30,
  sampleRate: number = 16000
): ArrayBuffer[] {
  const bytesPerSample = 2; // 16-bit = 2 bytes
  const chunkSize = Math.floor((chunkSizeMs * sampleRate) / 1000) * bytesPerSample;

  const chunks: ArrayBuffer[] = [];
  const uint8View = new Uint8Array(buffer);

  for (let i = 0; i < uint8View.length; i += chunkSize) {
    chunks.push(uint8View.slice(i, i + chunkSize).buffer);
  }

  return chunks;
}

/**
 * Decode base64 MP3 data to AudioBuffer.
 * @param base64 - Base64-encoded MP3 data
 * @param audioContext - Web Audio API context
 * @returns Promise resolving to decoded AudioBuffer
 */
export async function base64ToAudioBuffer(
  base64: string,
  audioContext: AudioContext
): Promise<AudioBuffer> {
  // Remove data URL prefix if present
  const base64Data = base64.includes(",") ? base64.split(",")[1] : base64;

  // Decode base64
  const binaryString = atob(base64Data);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }

  // Decode audio
  return audioContext.decodeAudioData(bytes.buffer);
}

/**
 * Convert ArrayBuffer to base64 string.
 * @param buffer - ArrayBuffer to encode
 * @returns Base64-encoded string
 */
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}
