import logging
import numpy as np
import torch
from typing import Tuple, Optional
from config import get_settings

logger = logging.getLogger(__name__)


class VADProcessor:
    """
    Silero VAD-based turn-taking engine.
    
    Processes continuous 30ms audio chunks and detects speech turns.
    Returns complete audio when silence threshold is met.
    """
    
    def __init__(self):
        settings = get_settings()
        self.threshold = settings.vad_threshold
        self.sample_rate = settings.vad_sample_rate
        self.audio_chunk_duration_ms = settings.audio_chunk_duration_ms
        
        # Calculate silence threshold in chunks
        # 600ms silence = 600 / 30 = 20 chunks
        self.silence_chunks_threshold = settings.vad_min_silence_duration_ms // settings.audio_chunk_duration_ms
        
        logger.info(f"Loading Silero VAD model...")
        try:
            self.model = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False
            )
            logger.info("Silero VAD model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD: {e}")
            raise
        
        # Initialize state
        self.audio_buffer = []
        self.is_speaking = False
        self.silence_chunks = 0
        self.speech_start_time = None
    
    def process_chunk(self, audio_chunk_bytes: bytes) -> Tuple[bool, Optional[bytes]]:
        """
        Process a 30ms audio chunk.
        
        Args:
            audio_chunk_bytes: 30ms of raw PCM audio (16-bit, 16kHz, mono)
        
        Returns:
            Tuple of (turn_complete: bool, audio_bytes: Optional[bytes])
            If turn_complete is True, audio_bytes contains the complete turn audio
        """
        try:
            # Convert PCM bytes to float32 tensor
            audio_int16 = np.frombuffer(audio_chunk_bytes, dtype=np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0
            audio_tensor = torch.FloatTensor(audio_float32)
            
            # Run VAD
            speech_prob = self.model(audio_tensor, self.sample_rate).item()
            
            if speech_prob >= self.threshold:
                # Speech detected
                if not self.is_speaking:
                    self.is_speaking = True
                    self.speech_start_time = None
                    logger.debug("Speech started")
                
                self.silence_chunks = 0
                self.audio_buffer.append(audio_chunk_bytes)
                return (False, None)
            
            elif self.is_speaking:
                # Was speaking, now silence detected
                self.silence_chunks += 1
                self.audio_buffer.append(audio_chunk_bytes)
                
                if self.silence_chunks >= self.silence_chunks_threshold:
                    # Enough silence -> turn is complete
                    logger.debug(f"Speech ended after {len(self.audio_buffer) * self.audio_chunk_duration_ms}ms")
                    
                    # Concatenate all buffered audio
                    complete_audio = b"".join(self.audio_buffer)
                    
                    # Reset state
                    self.audio_buffer = []
                    self.is_speaking = False
                    self.silence_chunks = 0
                    self.speech_start_time = None
                    
                    return (True, complete_audio)
                
                return (False, None)
            
            else:
                # Background silence, not recording
                return (False, None)
        
        except Exception as e:
            logger.error(f"VAD processing error: {e}")
            return (False, None)
    
    def reset(self) -> None:
        """Clear all buffers and state."""
        self.audio_buffer = []
        self.is_speaking = False
        self.silence_chunks = 0
        self.speech_start_time = None
        logger.debug("VAD processor reset")
