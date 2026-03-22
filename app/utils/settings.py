from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    app_name: str = "STT TTS API"
    app_version: str = "0.1.0"
    debug: bool = False
    max_upload_size_mb: int = 25

    # Deepgram
    deepgram_api_key: str = os.getenv("DEEPGRAM_API_KEY", "")
    deepgram_base_url: str = "https://api.deepgram.com/v1/listen"
    deepgram_model: str = "nova-3"

    # AssemblyAI
    assemblyai_api_key: str = os.getenv("ASSEMBLYAI_API_KEY", "")
    assemblyai_base_url: str = "https://api.assemblyai.com/v2"
    assemblyai_model: str = "best"

    # OpenAI (Whisper)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_stt_base_url: str = "https://api.openai.com/v1/audio/transcriptions"
    whisper_model: str = "whisper-1"

    # ElevenLabs
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    elevenlabs_base_url: str = "https://api.elevenlabs.io/v1/text-to-speech"
    elevenlabs_model: str = "eleven_multilingual_v2"
    elevenlabs_default_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    elevenlabs_stability: float = 0.5
    elevenlabs_similarity_boost: float = 0.75

    # Cartesia
    cartesia_api_key: str = os.getenv("CARTESIA_API_KEY", "")
    cartesia_base_url: str = "https://api.cartesia.ai/tts/bytes"
    cartesia_model: str = "sonic-3"
    cartesia_default_voice_id: str = "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"
    cartesia_api_version: str = "2024-06-10"
    cartesia_sample_rate: int = 44100

    # Default providers
    default_stt_provider: str = "deepgram"
    default_tts_provider: str = "elevenlabs"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
