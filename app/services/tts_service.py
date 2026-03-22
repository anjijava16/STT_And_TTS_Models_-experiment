from app.models.tts.base import BaseTTSModel
from app.models.tts.elevenlabs_model import ElevenLabsTTSModel
from app.models.tts.cartesia_model import CartesiaTTSModel
from app.schemas.tts import TTSProvider
from app.utils.settings import get_settings
from app.utils.exceptions import UnsupportedProviderError


_TTS_MODELS: dict[str, BaseTTSModel] = {
    TTSProvider.ELEVENLABS: ElevenLabsTTSModel(),
    TTSProvider.CARTESIA: CartesiaTTSModel(),
}


class TTSService:
    def _get_model(self, provider: TTSProvider | None) -> BaseTTSModel:
        provider_key = provider or TTSProvider(get_settings().default_tts_provider)
        model = _TTS_MODELS.get(provider_key)
        if not model:
            raise UnsupportedProviderError("TTS", provider_key)
        return model

    async def synthesize(
        self,
        text: str,
        provider: TTSProvider | None = None,
        voice_id: str | None = None,
        language: str = "en",
        output_format: str = "mp3",
    ) -> tuple[bytes, str]:
        """Returns (audio_bytes, content_type)"""
        tts_model = self._get_model(provider)
        return await tts_model.synthesize(text, voice_id, language, output_format)


tts_service = TTSService()
