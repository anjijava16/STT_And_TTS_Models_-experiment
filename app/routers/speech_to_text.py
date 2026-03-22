from fastapi import APIRouter, UploadFile, File, Form

from app.schemas.stt import STTProvider, STTResponse, STTErrorResponse
from app.services.stt_service import stt_service
from app.utils.exceptions import AudioFileError
from app.utils.settings import get_settings

router = APIRouter(prefix="/stt", tags=["Speech to Text"])

ALLOWED_AUDIO_TYPES = {
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/ogg",
    "audio/flac",
    "audio/webm",
    "audio/x-m4a",
}


@router.post(
    "/transcribe",
    response_model=STTResponse,
    responses={400: {"model": STTErrorResponse}, 502: {"model": STTErrorResponse}},
)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    provider: STTProvider | None = Form(default=None, description="STT provider to use"),
    language: str = Form(default="en", description="Language code"),
    model: str | None = Form(default=None, description="Model name override"),
):
    if audio.content_type and audio.content_type not in ALLOWED_AUDIO_TYPES:
        raise AudioFileError(f"Unsupported audio type: {audio.content_type}. Allowed: {', '.join(ALLOWED_AUDIO_TYPES)}")

    audio_data = await audio.read()
    max_size = get_settings().max_upload_size_bytes

    if len(audio_data) > max_size:
        raise AudioFileError(f"File too large. Maximum size: {get_settings().max_upload_size_mb}MB")

    if len(audio_data) == 0:
        raise AudioFileError("Empty audio file")

    return await stt_service.transcribe(
        audio_data=audio_data,
        provider=provider,
        language=language,
        model=model,
    )
