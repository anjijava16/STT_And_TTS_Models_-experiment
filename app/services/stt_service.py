from app.models.stt.base import BaseSTTModel
from app.models.stt.deepgram_model import DeepgramSTTModel
from app.models.stt.assemblyai_model import AssemblyAISTTModel
from app.models.stt.whisper_model import WhisperSTTModel
from app.schemas.stt import STTProvider, STTResponse
from app.utils.settings import get_settings
from app.utils.exceptions import UnsupportedProviderError


_STT_MODELS: dict[str, BaseSTTModel] = {
    STTProvider.DEEPGRAM: DeepgramSTTModel(),
    STTProvider.ASSEMBLYAI: AssemblyAISTTModel(),
    STTProvider.WHISPER: WhisperSTTModel(),
}


class STTService:
    def _get_model(self, provider: STTProvider | None) -> BaseSTTModel:
        provider_key = provider or STTProvider(get_settings().default_stt_provider)
        model = _STT_MODELS.get(provider_key)
        if not model:
            raise UnsupportedProviderError("STT", provider_key)
        return model

    async def transcribe(
        self,
        audio_data: bytes,
        provider: STTProvider | None = None,
        language: str = "en",
        model: str | None = None,
    ) -> STTResponse:
        print(f"STTService: Transcribing with provider={provider}, language={language}, model={model}"  )
        stt_model = self._get_model(provider)
        print(f"STTService: Using model {stt_model}")
        return await stt_model.transcribe(audio_data, language, model)


stt_service = STTService()
