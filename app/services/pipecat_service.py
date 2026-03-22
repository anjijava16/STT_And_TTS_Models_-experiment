import io
import wave
import asyncio
from typing import AsyncGenerator

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.pipeline.runner import PipelineRunner
from pipecat.frames.frames import (
    AudioRawFrame,
    EndFrame,
    Frame,
    TextFrame,
    TTSAudioRawFrame,
    TranscriptionFrame,
)
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.services.openai.tts import OpenAITTSService

from app.schemas.pipecat import (
    PipecatSTTProvider,
    PipecatTTSProvider,
    PipecatSTTResponse,
    PipecatTTSResponse,
    PipecatPipelineResponse,
)
from app.utils.settings import get_settings
from app.utils.exceptions import MissingAPIKeyError, STTProviderError, TTSProviderError


def _get_openai_key() -> str:
    key = get_settings().openai_api_key
    if not key:
        raise MissingAPIKeyError("openai")
    return key


def _build_stt_service(provider: PipecatSTTProvider, language: str, model: str | None) -> FrameProcessor:
    if provider == PipecatSTTProvider.OPENAI:
        return OpenAISTTService(
            api_key=_get_openai_key(),
            model=model or get_settings().whisper_model,
            language=language,
        )
    raise STTProviderError(provider, "Unsupported pipecat STT provider")


def _build_tts_service(
    provider: PipecatTTSProvider, voice: str, model: str | None, speed: float | None
) -> FrameProcessor:
    if provider == PipecatTTSProvider.OPENAI:
        kwargs = {
            "api_key": _get_openai_key(),
            "voice": voice,
        }
        if model:
            kwargs["model"] = model
        if speed:
            kwargs["speed"] = speed
        return OpenAITTSService(**kwargs)
    raise TTSProviderError(provider, "Unsupported pipecat TTS provider")


class ResultCollector(FrameProcessor):
    """Collects transcription and audio frames from the pipeline."""

    def __init__(self):
        super().__init__(name="ResultCollector")
        self.transcriptions: list[str] = []
        self.audio_chunks: list[bytes] = []
        self.sample_rate: int = 16000
        self.num_channels: int = 1

    async def process_frame(self, frame: Frame, direction):
        await super().process_frame(frame, direction)
        if isinstance(frame, TranscriptionFrame):
            self.transcriptions.append(frame.text)
        elif isinstance(frame, (TTSAudioRawFrame, AudioRawFrame)):
            self.audio_chunks.append(frame.audio)
            self.sample_rate = frame.sample_rate
            self.num_channels = frame.num_channels
        await self.push_frame(frame, direction)


def _pcm_to_wav(pcm_data: bytes, sample_rate: int, num_channels: int, sample_width: int = 2) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(num_channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()


def _wav_to_pcm(wav_data: bytes) -> tuple[bytes, int, int]:
    buf = io.BytesIO(wav_data)
    with wave.open(buf, "rb") as wf:
        sample_rate = wf.getframerate()
        num_channels = wf.getnchannels()
        pcm_data = wf.readframes(wf.getnframes())
    return pcm_data, sample_rate, num_channels


class PipecatService:
    """Orchestrates pipecat pipelines for STT, TTS, and full STT->TTS flows."""

    async def run_stt(
        self,
        audio_data: bytes,
        provider: PipecatSTTProvider,
        language: str = "en",
        model: str | None = None,
    ) -> PipecatSTTResponse:
        stt = _build_stt_service(provider, language, model)
        collector = ResultCollector()

        pipeline = Pipeline([stt, collector])
        task = PipelineTask(pipeline, params=PipelineParams(enable_metrics=False))
        runner = PipelineRunner(handle_sigint=False)

        # Convert wav to raw PCM for pipecat
        try:
            pcm_data, sample_rate, num_channels = _wav_to_pcm(audio_data)
        except Exception:
            # If not a valid wav, pass raw audio assuming 16kHz mono 16-bit PCM
            pcm_data = audio_data
            sample_rate = 16000
            num_channels = 1

        audio_frame = AudioRawFrame(audio=pcm_data, sample_rate=sample_rate, num_channels=num_channels)

        async def feed_audio():
            await task.queue_frame(audio_frame)
            await task.queue_frame(EndFrame())

        await asyncio.gather(runner.run(task), feed_audio())

        transcript = " ".join(collector.transcriptions).strip()
        return PipecatSTTResponse(
            provider=provider.value,
            transcript=transcript,
            language=language,
        )

    async def run_tts(
        self,
        text: str,
        provider: PipecatTTSProvider,
        voice: str = "alloy",
        model: str | None = None,
        speed: float | None = None,
    ) -> tuple[bytes, PipecatTTSResponse]:
        tts = _build_tts_service(provider, voice, model, speed)
        collector = ResultCollector()

        pipeline = Pipeline([tts, collector])
        task = PipelineTask(pipeline, params=PipelineParams(enable_metrics=False))
        runner = PipelineRunner(handle_sigint=False)

        async def feed_text():
            await task.queue_frame(TextFrame(text=text))
            await task.queue_frame(EndFrame())

        await asyncio.gather(runner.run(task), feed_text())

        pcm_audio = b"".join(collector.audio_chunks)
        wav_audio = _pcm_to_wav(pcm_audio, collector.sample_rate, collector.num_channels)

        response = PipecatTTSResponse(
            provider=provider.value,
            message="Speech synthesized via pipecat pipeline",
            audio_format="wav",
            audio_size_bytes=len(wav_audio),
        )
        return wav_audio, response

    async def run_pipeline(
        self,
        audio_data: bytes,
        stt_provider: PipecatSTTProvider,
        tts_provider: PipecatTTSProvider,
        language: str = "en",
        voice: str = "alloy",
        tts_model: str | None = None,
        speed: float | None = None,
    ) -> tuple[bytes, PipecatPipelineResponse]:
        """Full pipeline: audio -> STT -> TTS -> audio."""
        stt = _build_stt_service(stt_provider, language, model=None)
        tts = _build_tts_service(tts_provider, voice, tts_model, speed)
        collector = ResultCollector()

        pipeline = Pipeline([stt, tts, collector])
        task = PipelineTask(pipeline, params=PipelineParams(enable_metrics=False))
        runner = PipelineRunner(handle_sigint=False)

        try:
            pcm_data, sample_rate, num_channels = _wav_to_pcm(audio_data)
        except Exception:
            pcm_data = audio_data
            sample_rate = 16000
            num_channels = 1

        audio_frame = AudioRawFrame(audio=pcm_data, sample_rate=sample_rate, num_channels=num_channels)

        async def feed_audio():
            await task.queue_frame(audio_frame)
            await task.queue_frame(EndFrame())

        await asyncio.gather(runner.run(task), feed_audio())

        transcript = " ".join(collector.transcriptions).strip()
        pcm_audio = b"".join(collector.audio_chunks)
        wav_audio = _pcm_to_wav(pcm_audio, collector.sample_rate, collector.num_channels)

        response = PipecatPipelineResponse(
            stt_provider=stt_provider.value,
            tts_provider=tts_provider.value,
            transcript=transcript,
            audio_format="wav",
            audio_size_bytes=len(wav_audio),
        )
        return wav_audio, response


pipecat_service = PipecatService()
