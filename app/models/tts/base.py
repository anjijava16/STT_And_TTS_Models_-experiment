from abc import ABC, abstractmethod


class BaseTTSModel(ABC):
    provider_name: str

    @abstractmethod
    async def synthesize(
        self, text: str, voice_id: str | None, language: str, output_format: str
    ) -> tuple[bytes, str]:
        """Returns (audio_bytes, content_type)"""
        pass
