from pydantic import BaseModel, Field
from enum import Enum


class STTProvider(str, Enum):
    DEEPGRAM = "deepgram"
    ASSEMBLYAI = "assemblyai"
    WHISPER = "whisper"


class STTRequest(BaseModel):
    provider: STTProvider | None = None
    language: str = Field(default="en", description="Language code for transcription")
    model: str | None = Field(default=None, description="Model name override for the provider")


class STTResponse(BaseModel):
    provider: str
    transcript: str
    confidence: float | None = None
    language: str | None = None
    duration: float | None = None


class STTErrorResponse(BaseModel):
    detail: str
