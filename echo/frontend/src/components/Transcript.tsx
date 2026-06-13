import React, { useEffect, useRef } from "react";
import { TranscriptEntry } from "../types";
import "./Transcript.css";

interface TranscriptProps {
  entries: TranscriptEntry[];
}

export function Transcript({ entries }: TranscriptProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new entries
  useEffect(() => {
    if (scrollContainerRef.current) {
      setTimeout(() => {
        scrollContainerRef.current?.scrollTo({
          top: scrollContainerRef.current.scrollHeight,
          behavior: "smooth",
        });
      }, 0);
    }
  }, [entries]);

  return (
    <div className="transcript-container" ref={scrollContainerRef}>
      {entries.length === 0 ? (
        <div className="transcript-empty">No conversation yet. Click "Start Talking" to begin.</div>
      ) : (
        <div className="transcript-messages">
          {entries.map((entry) => (
            <div
              key={entry.id}
              className={`transcript-entry transcript-${entry.role}`}
            >
              <div className="transcript-bubble">
                <p className="transcript-text">{entry.text}</p>
                <span className="transcript-timestamp">
                  {entry.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  })}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
