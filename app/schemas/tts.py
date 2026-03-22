from pydantic import BaseModel, Field
from enum import Enum


class TTSProvider(str, Enum):
    ELEVENLABS = "elevenlabs"
    CARTESIA = "cartesia"


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    provider: TTSProvider | None = None
    voice_id: str | None = Field(default='JBFqnCBsd6RMkjVDRZzb', description="Voice ID for the provider")
    language: str = Field(default="en", description="Language code")
    output_format: str = Field(default="mp3", description="Output audio format (mp3, wav, pcm)")


class TTSResponse(BaseModel):
    provider: str
    message: str
    audio_format: str
    audio_size_bytes: int


class TTSErrorResponse(BaseModel):
    detail: str
