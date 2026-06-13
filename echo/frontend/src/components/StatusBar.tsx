import React from "react";
import { AgentState } from "../types";
import "./StatusBar.css";

interface StatusBarProps {
  isConnected: boolean;
  state: AgentState;
}

export function StatusBar({ isConnected, state }: StatusBarProps) {
  const statusText = isConnected ? getStatusText(state) : "Disconnected";
  const statusClass = isConnected ? `status-${state}` : "status-error";

  return (
    <div className={`status-bar ${statusClass}`}>
      <div className="status-dot"></div>
      <span className="status-text">{statusText}</span>
    </div>
  );
}

function getStatusText(state: AgentState): string {
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
      return "Error occurred";
    default:
      return "Connecting...";
  }
}
