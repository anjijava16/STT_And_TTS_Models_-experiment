import httpx

from app.models.stt.base import BaseSTTModel
from app.schemas.stt import STTResponse
from app.utils.settings import get_settings
from app.utils.exceptions import STTProviderError, MissingAPIKeyError


class DeepgramSTTModel(BaseSTTModel):
    provider_name = "deepgram"

    def _get_api_key(self) -> str:
        key = get_settings().deepgram_api_key
        if not key:
            raise MissingAPIKeyError(self.provider_name)
        return key

    async def transcribe(self, audio_data: bytes, language: str, model: str | None = None) -> STTResponse:
        api_key = self._get_api_key()
        settings = get_settings()

        params = {
            "language": language,
            "model": model or settings.deepgram_model,
            "smart_format": "true",
        }
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "audio/wav",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    settings.deepgram_base_url,
                    headers=headers,
                    params=params,
                    content=audio_data,
                )
                response.raise_for_status()
                data = response.json()

            result = data["results"]["channels"][0]["alternatives"][0]
            return STTResponse(
                provider=self.provider_name,
                transcript=result["transcript"],
                confidence=result.get("confidence"),
                language=language,
                duration=data.get("metadata", {}).get("duration"),
            )
        except httpx.HTTPStatusError as e:
            raise STTProviderError(self.provider_name, f"HTTP {e.response.status_code}: {e.response.text}")
        except (KeyError, IndexError) as e:
            raise STTProviderError(self.provider_name, f"Unexpected response format: {e}")
        except httpx.RequestError as e:
            raise STTProviderError(self.provider_name, f"Connection error: {e}")
