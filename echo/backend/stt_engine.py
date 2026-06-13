import logging
import time
import numpy as np
from faster_whisper import WhisperModel
from config import get_settings

logger = logging.getLogger(__name__)

# Global singleton instance
_engine = None


class STTEngine:
    """Speech-to-Text engine using faster-whisper."""
    
    def __init__(self):
        settings = get_settings()
        logger.info(f"Loading Whisper model: {settings.whisper_model_size}")
        
        start_time = time.time()
        self.model = WhisperModel(
            model_size_or_path=settings.whisper_model_size,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
            download_root=".cache/whisper"
        )
        load_time = (time.time() - start_time) * 1000
        logger.info(f"Whisper model loaded in {load_time:.2f}ms")
    
    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribe raw PCM audio bytes (16-bit, 16kHz, mono) to text.
        
        Args:
            audio_bytes: Raw PCM audio data
        
        Returns:
            Transcribed text, or empty string if no meaningful speech detected
        """
        try:
            # Convert raw PCM bytes to float32 array
            audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0
            
            start_time = time.time()
            
            # Run whisper transcription
            segments, info = self.model.transcribe(
                audio_float32,
                language="en",
                beam_size=1,
                vad_filter=False
            )
            
            # Join all segment texts
            transcript_text = " ".join([segment.text for segment in segments]).strip()
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"STT completed in {duration_ms:.2f}ms: '{transcript_text}'")
            
            # Return empty string if transcription is blank or only punctuation
            if not transcript_text or transcript_text.replace(".", "").replace("?", "").replace("!", "").strip() == "":
                return ""
            
            return transcript_text
        
        except Exception as e:
            logger.error(f"STT transcription error: {e}")
            return ""


def get_stt_engine() -> STTEngine:
    """Get or create the singleton STT engine instance."""
    global _engine
    if _engine is None:
        _engine = STTEngine()
    return _engine
