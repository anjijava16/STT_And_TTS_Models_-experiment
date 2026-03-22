from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import Response

from app.schemas.pipecat import (
    PipecatSTTProvider,
    PipecatTTSProvider,
    PipecatSTTResponse,
    PipecatTTSRequest,
    PipecatTTSResponse,
    PipecatPipelineResponse,
)
from app.services.pipecat_service import pipecat_service
from app.utils.exceptions import AudioFileError
from app.utils.settings import get_settings

router = APIRouter(prefix="/pipecat", tags=["Pipecat Pipeline"])

ALLOWED_AUDIO_TYPES = {
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/flac",
    "audio/webm",
}


@router.post(
    "/stt",
    response_model=PipecatSTTResponse,
    summary="Speech-to-Text via Pipecat pipeline",
)
async def pipecat_stt(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    provider: PipecatSTTProvider = Form(default=PipecatSTTProvider.OPENAI),
    language: str = Form(default="en"),
    model: str | None = Form(default=None, description="STT model override"),
):
    if audio.content_type and audio.content_type not in ALLOWED_AUDIO_TYPES:
        raise AudioFileError(f"Unsupported audio type: {audio.content_type}")

    audio_data = await audio.read()
    max_size = get_settings().max_upload_size_bytes
    if len(audio_data) > max_size:
        raise AudioFileError(f"File too large. Maximum size: {get_settings().max_upload_size_mb}MB")
    if not audio_data:
        raise AudioFileError("Empty audio file")

    return await pipecat_service.run_stt(
        audio_data=audio_data,
        provider=provider,
        language=language,
        model=model,
    )


@router.post(
    "/tts",
    summary="Text-to-Speech via Pipecat pipeline",
    responses={200: {"content": {"audio/wav": {}}}},
)
async def pipecat_tts(request: PipecatTTSRequest):
    audio_bytes, metadata = await pipecat_service.run_tts(
        text=request.text,
        provider=request.provider,
        voice=request.voice,
        model=request.model,
        speed=request.speed,
    )

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=pipecat_speech.wav"},
    )


@router.post(
    "/tts/metadata",
    response_model=PipecatTTSResponse,
    summary="Text-to-Speech metadata via Pipecat pipeline",
)
async def pipecat_tts_metadata(request: PipecatTTSRequest):
    _, metadata = await pipecat_service.run_tts(
        text=request.text,
        provider=request.provider,
        voice=request.voice,
        model=request.model,
        speed=request.speed,
    )
    return metadata


@router.post(
    "/pipeline",
    summary="Full STT -> TTS pipeline via Pipecat",
    responses={200: {"content": {"audio/wav": {}}}},
)
async def pipecat_pipeline(
    audio: UploadFile = File(..., description="Audio file to process through pipeline"),
    stt_provider: PipecatSTTProvider = Form(default=PipecatSTTProvider.OPENAI),
    tts_provider: PipecatTTSProvider = Form(default=PipecatTTSProvider.OPENAI),
    language: str = Form(default="en"),
    voice: str = Form(default="alloy"),
    tts_model: str | None = Form(default=None),
    speed: float | None = Form(default=None, ge=0.25, le=4.0),
):
    if audio.content_type and audio.content_type not in ALLOWED_AUDIO_TYPES:
        raise AudioFileError(f"Unsupported audio type: {audio.content_type}")

    audio_data = await audio.read()
    max_size = get_settings().max_upload_size_bytes
    if len(audio_data) > max_size:
        raise AudioFileError(f"File too large. Maximum size: {get_settings().max_upload_size_mb}MB")
    if not audio_data:
        raise AudioFileError("Empty audio file")

    audio_bytes, _ = await pipecat_service.run_pipeline(
        audio_data=audio_data,
        stt_provider=stt_provider,
        tts_provider=tts_provider,
        language=language,
        voice=voice,
        tts_model=tts_model,
        speed=speed,
    )

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=pipecat_pipeline.wav"},
    )


@router.post(
    "/pipeline/metadata",
    response_model=PipecatPipelineResponse,
    summary="Full STT -> TTS pipeline metadata via Pipecat",
)
async def pipecat_pipeline_metadata(
    audio: UploadFile = File(..., description="Audio file to process through pipeline"),
    stt_provider: PipecatSTTProvider = Form(default=PipecatSTTProvider.OPENAI),
    tts_provider: PipecatTTSProvider = Form(default=PipecatTTSProvider.OPENAI),
    language: str = Form(default="en"),
    voice: str = Form(default="alloy"),
    tts_model: str | None = Form(default=None),
    speed: float | None = Form(default=None, ge=0.25, le=4.0),
):
    if audio.content_type and audio.content_type not in ALLOWED_AUDIO_TYPES:
        raise AudioFileError(f"Unsupported audio type: {audio.content_type}")

    audio_data = await audio.read()
    max_size = get_settings().max_upload_size_bytes
    if len(audio_data) > max_size:
        raise AudioFileError(f"File too large. Maximum size: {get_settings().max_upload_size_mb}MB")
    if not audio_data:
        raise AudioFileError("Empty audio file")

    _, metadata = await pipecat_service.run_pipeline(
        audio_data=audio_data,
        stt_provider=stt_provider,
        tts_provider=tts_provider,
        language=language,
        voice=voice,
        tts_model=tts_model,
        speed=speed,
    )

    return metadata
