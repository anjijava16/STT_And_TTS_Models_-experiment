import httpx

from app.models.tts.base import BaseTTSModel
from app.utils.settings import get_settings
from app.utils.exceptions import TTSProviderError, MissingAPIKeyError


CARTESIA_FORMAT_MAP = {
    "mp3": {"format": "mp3", "content_type": "audio/mpeg"},
    "wav": {"format": "wav", "content_type": "audio/wav"},
    "pcm": {"format": "raw", "content_type": "audio/pcm"},
}


class CartesiaTTSModel(BaseTTSModel):
    provider_name = "cartesia"

    def _get_api_key(self) -> str:
        key = get_settings().cartesia_api_key
        if not key:
            raise MissingAPIKeyError(self.provider_name)
        return key

    async def synthesize(
        self, text: str, voice_id: str | None, language: str, output_format: str
    ) -> tuple[bytes, str]:
        api_key = self._get_api_key()
        settings = get_settings()
        voice = voice_id or settings.cartesia_default_voice_id
        fmt = CARTESIA_FORMAT_MAP.get(output_format, CARTESIA_FORMAT_MAP["mp3"])

        headers = {
            "X-API-Key": api_key,
            "Cartesia-Version": settings.cartesia_api_version,
            "Content-Type": "application/json",
        }
        payload = {
            "transcript": text,
            "model_id": settings.cartesia_model,
            "voice": {
                "mode": "id",
                "id": voice,
            },
            "language": language,
            "output_format": {
                "container": fmt["format"],
                "encoding": "pcm_f32le" if fmt["format"] == "raw" else "mp3" if fmt["format"] == "mp3" else "pcm_f32le",
                "sample_rate": settings.cartesia_sample_rate,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    settings.cartesia_base_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                return response.content, fmt["content_type"]
        except httpx.HTTPStatusError as e:
            raise TTSProviderError(self.provider_name, f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise TTSProviderError(self.provider_name, f"Connection error: {e}")
