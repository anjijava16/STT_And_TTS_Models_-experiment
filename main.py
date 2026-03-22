import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.utils.settings import get_settings
from app.routers import health, speech_to_text, text_to_speech, pipecat

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for Speech-to-Text and Text-to-Speech using multiple providers",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(speech_to_text.router, prefix="/api/v1")
app.include_router(text_to_speech.router, prefix="/api/v1")
app.include_router(pipecat.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8047, reload=settings.debug)
