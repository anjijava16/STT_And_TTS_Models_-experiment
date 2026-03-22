import httpx

from app.models.stt.base import BaseSTTModel
from app.schemas.stt import STTResponse
from app.utils.settings import get_settings
from app.utils.exceptions import STTProviderError, MissingAPIKeyError


class WhisperSTTModel(BaseSTTModel):
    provider_name = "whisper"

    def _get_api_key(self) -> str:
        key = get_settings().openai_api_key
        if not key:
            raise MissingAPIKeyError(self.provider_name)
        return key

    async def transcribe(self, audio_data: bytes, language: str, model: str | None = None) -> STTResponse:
        api_key = self._get_api_key()
        settings = get_settings()

        headers = {"Authorization": f"Bearer {api_key}"}
        files = {"file": ("audio.wav", audio_data, "audio/wav")}
        data = {
            "model": model or settings.whisper_model,
            "language": language,
            "response_format": "verbose_json",
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    settings.openai_stt_base_url,
                    headers=headers,
                    files=files,
                    data=data,
                )
                response.raise_for_status()
                result = response.json()

            return STTResponse(
                provider=self.provider_name,
                transcript=result["text"],
                confidence=None,
                language=result.get("language", language),
                duration=result.get("duration"),
            )
        except httpx.HTTPStatusError as e:
            raise STTProviderError(self.provider_name, f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise STTProviderError(self.provider_name, f"Connection error: {e}")
