import React from "react";
import { LatencyMetrics } from "../types";
import "./LatencyBadge.css";

interface LatencyBadgeProps {
  metrics: LatencyMetrics | null;
}

export function LatencyBadge({ metrics }: LatencyBadgeProps) {
  if (!metrics) return null;

  const isGood = metrics.total_ms < 800;
  const icon = isGood ? "✓" : "⚠";

  return (
    <div className={`latency-badge ${isGood ? "latency-good" : "latency-warning"}`}>
      <span className="latency-item">STT {Math.round(metrics.stt_ms)}ms</span>
      <span className="latency-separator">|</span>
      <span className="latency-item">LLM {Math.round(metrics.llm_ms)}ms</span>
      <span className="latency-separator">|</span>
      <span className="latency-item">TTS {Math.round(metrics.tts_ms)}ms</span>
      <span className="latency-separator">|</span>
      <span className="latency-item latency-total">
        Total {Math.round(metrics.total_ms)}ms {icon}
      </span>
    </div>
  );
}
