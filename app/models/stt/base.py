from abc import ABC, abstractmethod
from app.schemas.stt import STTResponse


class BaseSTTModel(ABC):
    provider_name: str

    @abstractmethod
    async def transcribe(self, audio_data: bytes, language: str, model: str | None = None) -> STTResponse:
        pass
