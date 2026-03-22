import httpx

from app.models.tts.base import BaseTTSModel
from app.utils.settings import get_settings
from app.utils.exceptions import TTSProviderError, MissingAPIKeyError


ELEVENLABS_FORMAT_MAP = {
    "mp3": {"output_format": "mp3_44100_128", "content_type": "audio/mpeg"},
    "wav": {"output_format": "pcm_44100", "content_type": "audio/wav"},
    "pcm": {"output_format": "pcm_44100", "content_type": "audio/pcm"},
}


class ElevenLabsTTSModel(BaseTTSModel):
    provider_name = "elevenlabs"

    def _get_api_key(self) -> str:
        key = get_settings().elevenlabs_api_key
        if not key:
            raise MissingAPIKeyError(self.provider_name)
        return key

    async def synthesize(
        self, text: str, voice_id: str | None, language: str, output_format: str
    ) -> tuple[bytes, str]:
        api_key = self._get_api_key()
        settings = get_settings()
        voice = voice_id or settings.elevenlabs_default_voice_id
        fmt = ELEVENLABS_FORMAT_MAP.get(output_format, ELEVENLABS_FORMAT_MAP["mp3"])

        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": settings.elevenlabs_model,
            "voice_settings": {
                "stability": settings.elevenlabs_stability,
                "similarity_boost": settings.elevenlabs_similarity_boost,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{settings.elevenlabs_base_url}/{voice}",
                    headers=headers,
                    json=payload,
                    params={"output_format": fmt["output_format"]},
                )
                response.raise_for_status()
                return response.content, fmt["content_type"]
        except httpx.HTTPStatusError as e:
            raise TTSProviderError(self.provider_name, f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise TTSProviderError(self.provider_name, f"Connection error: {e}")
