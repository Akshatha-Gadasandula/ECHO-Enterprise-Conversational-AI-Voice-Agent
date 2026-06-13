export type AgentState = "idle" | "listening" | "processing" | "speaking" | "error";

export interface TranscriptEntry {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: Date;
}

export interface LatencyMetrics {
  stt_ms: number;
  llm_ms: number;
  tts_ms: number;
  total_ms: number;
}

export type ServerMessage =
  | { type: "session_ready"; conversation_id: string }
  | { type: "transcript"; text: string; role: "user" | "assistant" }
  | { type: "audio_response"; data: string; format: string }
  | {
      type: "latency";
      stt_ms: number;
      llm_ms: number;
      tts_ms: number;
      total_ms: number;
    }
  | { type: "status"; state: AgentState }
  | { type: "error"; message: string };
