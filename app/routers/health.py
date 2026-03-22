from fastapi import APIRouter
from app.utils.settings import get_settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    settings = get_settings()
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/providers")
async def providers_status():
    settings = get_settings()
    return {
        "stt_providers": {
            "deepgram": {"configured": bool(settings.deepgram_api_key)},
            "assemblyai": {"configured": bool(settings.assemblyai_api_key)},
            "whisper": {"configured": bool(settings.openai_api_key)},
        },
        "tts_providers": {
            "elevenlabs": {"configured": bool(settings.elevenlabs_api_key)},
            "cartesia": {"configured": bool(settings.cartesia_api_key)},
        },
        "defaults": {
            "stt_provider": settings.default_stt_provider,
            "tts_provider": settings.default_tts_provider,
        },
    }
