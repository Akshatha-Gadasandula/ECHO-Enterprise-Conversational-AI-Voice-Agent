import React, { useMemo } from "react";
import { AgentState } from "../types";
import "./VoiceOrb.css";

interface VoiceOrbProps {
  state: AgentState;
}

export function VoiceOrb({ state }: VoiceOrbProps) {
  const animationClass = useMemo(() => {
    switch (state) {
      case "idle":
        return "orb-idle";
      case "listening":
        return "orb-listening";
      case "processing":
        return "orb-processing";
      case "speaking":
        return "orb-speaking";
      case "error":
        return "orb-error";
      default:
        return "orb-idle";
    }
  }, [state]);

  const stateLabel = useMemo(() => {
    switch (state) {
      case "idle":
        return "Ready to listen";
      case "listening":
        return "Listening...";
      case "processing":
        return "Thinking...";
      case "speaking":
        return "Speaking...";
      case "error":
        return "Error";
      default:
        return "Idle";
    }
  }, [state]);

  return (
    <div className="voice-orb-container">
      <svg className={`voice-orb ${animationClass}`} viewBox="0 0 200 200" width="200" height="200">
        <defs>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <style>{`
            @keyframes pulse {
              0%, 100% { r: 60px; opacity: 1; }
              50% { r: 65px; opacity: 0.8; }
            }
            @keyframes ripple {
              0% { r: 60px; opacity: 1; }
              100% { r: 90px; opacity: 0; }
            }
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
            @keyframes glow-pulse {
              0%, 100% { filter: drop-shadow(0 0 10px #6366F1); }
              50% { filter: drop-shadow(0 0 20px #818CF8); }
            }
            .orb-idle circle { animation: pulse 3s ease-in-out infinite; }
            .orb-listening circle:nth-child(1) { animation: ripple 1s ease-out infinite; }
            .orb-listening circle:nth-child(2) { animation: ripple 1s ease-out 0.3s infinite; }
            .orb-listening circle:nth-child(3) { animation: ripple 1s ease-out 0.6s infinite; }
            .orb-processing { animation: spin 2s linear infinite; }
            .orb-speaking circle { animation: glow-pulse 1s ease-in-out infinite; }
            .orb-error circle { fill: #EF4444; }
          `}</style>
        </defs>

        {/* Idle state: single pulsing circle */}
        {state === "idle" && (
          <circle cx="100" cy="100" r="60" fill="#6366F1" filter="url(#glow)" opacity="0.9" />
        )}

        {/* Listening state: ripple rings */}
        {state === "listening" && (
          <>
            <circle cx="100" cy="100" r="60" fill="#6366F1" filter="url(#glow)" />
            <circle cx="100" cy="100" r="60" fill="none" stroke="#818CF8" strokeWidth="2" opacity="0.6" />
            <circle cx="100" cy="100" r="60" fill="none" stroke="#818CF8" strokeWidth="2" opacity="0.4" />
            <circle cx="100" cy="100" r="60" fill="none" stroke="#818CF8" strokeWidth="2" opacity="0.2" />
          </>
        )}

        {/* Processing state: rotating arc */}
        {state === "processing" && (
          <>
            <circle cx="100" cy="100" r="60" fill="none" stroke="#6366F1" strokeWidth="3" strokeDasharray="188 314" />
          </>
        )}

        {/* Speaking state: concentric rings with glow */}
        {state === "speaking" && (
          <>
            <circle cx="100" cy="100" r="50" fill="none" stroke="#818CF8" strokeWidth="1" opacity="0.4" />
            <circle cx="100" cy="100" r="60" fill="#6366F1" filter="url(#glow)" opacity="0.9" />
            <circle cx="100" cy="100" r="70" fill="none" stroke="#818CF8" strokeWidth="1" opacity="0.3" />
            <circle cx="100" cy="100" r="80" fill="none" stroke="#818CF8" strokeWidth="1" opacity="0.2" />
          </>
        )}

        {/* Error state: red circle with shake */}
        {state === "error" && (
          <circle cx="100" cy="100" r="60" fill="#EF4444" filter="url(#glow)" opacity="0.9" />
        )}
      </svg>

      <p className="orb-label">{stateLabel}</p>
    </div>
  );
}
