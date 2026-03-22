from pydantic import BaseModel, Field
from enum import Enum


class PipecatSTTProvider(str, Enum):
    OPENAI = "openai"


class PipecatTTSProvider(str, Enum):
    OPENAI = "openai"


class PipecatSTTRequest(BaseModel):
    """STT request using pipecat pipeline."""

    provider: PipecatSTTProvider = PipecatSTTProvider.OPENAI
    language: str = Field(default="en", description="Language code")
    model: str | None = Field(default=None, description="STT model override")


class PipecatTTSRequest(BaseModel):
    """TTS request using pipecat pipeline."""

    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    provider: PipecatTTSProvider = PipecatTTSProvider.OPENAI
    voice: str = Field(default="alloy", description="Voice name (alloy, echo, fable, onyx, nova, shimmer)")
    model: str | None = Field(default=None, description="TTS model override")
    speed: float | None = Field(default=None, ge=0.25, le=4.0, description="Speech speed")


class PipecatPipelineRequest(BaseModel):
    """Full pipeline: audio in -> STT -> TTS -> audio out."""

    stt_provider: PipecatSTTProvider = PipecatSTTProvider.OPENAI
    tts_provider: PipecatTTSProvider = PipecatTTSProvider.OPENAI
    language: str = Field(default="en", description="Language code")
    voice: str = Field(default="alloy", description="TTS voice name")
    tts_model: str | None = Field(default=None, description="TTS model override")
    speed: float | None = Field(default=None, ge=0.25, le=4.0, description="TTS speech speed")


class PipecatSTTResponse(BaseModel):
    provider: str
    transcript: str
    language: str | None = None


class PipecatTTSResponse(BaseModel):
    provider: str
    message: str
    audio_format: str
    audio_size_bytes: int


class PipecatPipelineResponse(BaseModel):
    stt_provider: str
    tts_provider: str
    transcript: str
    audio_format: str
    audio_size_bytes: int
