import logging
import time
from typing import AsyncGenerator
from elevenlabs.client import ElevenLabs
from config import get_settings

logger = logging.getLogger(__name__)

# Global singleton instance
_engine = None


class TTSEngine:
    """Text-to-Speech engine using ElevenLabs."""
    
    def __init__(self):
        settings = get_settings()
        logger.info("Initializing ElevenLabs TTS engine")
        
        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        self.voice_id = settings.elevenlabs_voice_id
        self.model_id = settings.tts_model_id
        self.output_format = settings.tts_output_format
    
    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize text to speech and return full audio bytes.
        
        Args:
            text: Text to synthesize
        
        Returns:
            MP3 audio bytes
        """
        try:
            start_time = time.time()
            
            # Generate audio
            audio = self.client.generate(
                text=text,
                voice=self.voice_id,
                model=self.model_id,
                stream=False
            )
            
            # audio is a generator, collect all bytes
            audio_bytes = b"".join(audio)
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"TTS synthesized in {duration_ms:.2f}ms ({len(audio_bytes)} bytes): '{text[:50]}...'")
            
            return audio_bytes
        
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return b""
    
    async def synthesize_streaming(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Synthesize text to speech with streaming chunks.
        
        Args:
            text: Text to synthesize
        
        Yields:
            MP3 audio chunks as they arrive
        """
        try:
            start_time = time.time()
            chunk_count = 0
            
            # Generate audio with streaming
            audio_stream = self.client.generate(
                text=text,
                voice=self.voice_id,
                model=self.model_id,
                stream=True
            )
            
            async for chunk in audio_stream:
                chunk_count += 1
                yield chunk
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"TTS streamed {chunk_count} chunks in {duration_ms:.2f}ms: '{text[:50]}...'")
        
        except Exception as e:
            logger.error(f"TTS streaming error: {e}")


def get_tts_engine() -> TTSEngine:
    """Get or create the singleton TTS engine instance."""
    global _engine
    if _engine is None:
        _engine = TTSEngine()
    return _engine
