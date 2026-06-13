from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API Keys
    groq_api_key: str
    elevenlabs_api_key: str
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice

    # STT config
    whisper_model_size: str = "base.en"  # Options: tiny.en, base.en, small.en
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    # VAD config
    vad_threshold: float = 0.5
    vad_min_silence_duration_ms: int = 600   # ms of silence before turn ends
    vad_speech_pad_ms: int = 100
    vad_sample_rate: int = 16000
    audio_chunk_duration_ms: int = 30        # VAD processes 30ms chunks

    # LLM config
    groq_model: str = "llama-3.1-8b-instant"  # Fastest Groq model for low latency voice
    max_tokens: int = 256                    # Keep responses concise for voice
    conversation_memory_turns: int = 10

    # RAG config
    embedding_model: str = "all-MiniLM-L6-v2"
    rag_top_k: int = 3
    faiss_index_path: str = "rag/faiss_index"

    # TTS config
    tts_model_id: str = "eleven_turbo_v2"   # Lowest latency ElevenLabs model
    tts_output_format: str = "mp3_44100_128"

    # Server config
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
