import time
from typing import Dict


class LatencyTracker:
    """Tracks latency measurements for different processing stages."""
    
    def __init__(self):
        self.measurements: Dict[str, Dict[str, float]] = {}
        self.start_times: Dict[str, float] = {}
    
    def start(self, label: str) -> None:
        """Record the start time for a stage (e.g., 'stt', 'llm', 'tts')."""
        self.start_times[label] = time.perf_counter()
    
    def end(self, label: str) -> float:
        """Record the end time and return duration in milliseconds."""
        if label not in self.start_times:
            return 0.0
        
        end_time = time.perf_counter()
        start_time = self.start_times[label]
        duration_ms = (end_time - start_time) * 1000
        
        if label not in self.measurements:
            self.measurements[label] = {}
        
        self.measurements[label]["duration_ms"] = duration_ms
        del self.start_times[label]
        
        return duration_ms
    
    def summary(self) -> Dict[str, float]:
        """Return all measured durations plus total_ms."""
        summary_dict = {
            "stt_ms": self.measurements.get("stt", {}).get("duration_ms", 0.0),
            "llm_ms": self.measurements.get("llm", {}).get("duration_ms", 0.0),
            "tts_ms": self.measurements.get("tts", {}).get("duration_ms", 0.0),
        }
        
        # Calculate total as sum of all measured stages
        total_ms = sum([v for k, v in summary_dict.items() if v > 0])
        summary_dict["total_ms"] = total_ms
        
        return summary_dict
    
    def reset(self) -> None:
        """Clear all measurements."""
        self.measurements = {}
        self.start_times = {}
