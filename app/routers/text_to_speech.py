from fastapi import APIRouter
from fastapi.responses import Response

from app.schemas.tts import TTSRequest, TTSResponse, TTSErrorResponse
from app.services.tts_service import tts_service

router = APIRouter(prefix="/tts", tags=["Text to Speech"])


@router.post(
    "/synthesize",
    responses={
        200: {"content": {"audio/mpeg": {}, "audio/wav": {}, "audio/pcm": {}}},
        400: {"model": TTSErrorResponse},
        502: {"model": TTSErrorResponse},
    },
)
async def synthesize_speech(request: TTSRequest):
    audio_bytes, content_type = await tts_service.synthesize(
        text=request.text,
        provider=request.provider,
        voice_id=request.voice_id,
        language=request.language,
        output_format=request.output_format,
    )

    return Response(
        content=audio_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename=speech.{request.output_format}",
        },
    )


@router.post(
    "/synthesize/metadata",
    response_model=TTSResponse,
    responses={400: {"model": TTSErrorResponse}, 502: {"model": TTSErrorResponse}},
)
async def synthesize_speech_metadata(request: TTSRequest):
    audio_bytes, _ = await tts_service.synthesize(
        text=request.text,
        provider=request.provider,
        voice_id=request.voice_id,
        language=request.language,
        output_format=request.output_format,
    )

    return TTSResponse(
        provider=request.provider.value if request.provider else "default",
        message="Speech synthesized successfully",
        audio_format=request.output_format,
        audio_size_bytes=len(audio_bytes),
    )
