import httpx

from app.models.stt.base import BaseSTTModel
from app.schemas.stt import STTResponse
from app.utils.settings import get_settings
from app.utils.exceptions import STTProviderError, MissingAPIKeyError


class AssemblyAISTTModel(BaseSTTModel):
    provider_name = "assemblyai"

    def _get_api_key(self) -> str:
        key = get_settings().assemblyai_api_key
        if not key:
            raise MissingAPIKeyError(self.provider_name)
        return key

    async def transcribe(self, audio_data: bytes, language: str, model: str | None = None) -> STTResponse:
        api_key = self._get_api_key()
        settings = get_settings()
        headers = {"Authorization": api_key}

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Step 1: Upload audio
                upload_response = await client.post(
                    f"{settings.assemblyai_base_url}/upload",
                    headers=headers,
                    content=audio_data,
                )
                upload_response.raise_for_status()
                audio_url = upload_response.json()["upload_url"]

                # Step 2: Create transcription
                transcript_request = {
                    "audio_url": audio_url,
                    "language_code": language,
                    "speech_model": model or settings.assemblyai_model,
                }

                transcript_response = await client.post(
                    f"{settings.assemblyai_base_url}/transcript",
                    headers=headers,
                    json=transcript_request,
                )
                transcript_response.raise_for_status()
                transcript_id = transcript_response.json()["id"]

                # Step 3: Poll for completion
                import asyncio
                while True:
                    poll_response = await client.get(
                        f"{settings.assemblyai_base_url}/transcript/{transcript_id}",
                        headers=headers,
                    )
                    poll_response.raise_for_status()
                    poll_data = poll_response.json()

                    if poll_data["status"] == "completed":
                        return STTResponse(
                            provider=self.provider_name,
                            transcript=poll_data["text"] or "",
                            confidence=poll_data.get("confidence"),
                            language=language,
                            duration=poll_data.get("audio_duration"),
                        )
                    elif poll_data["status"] == "error":
                        raise STTProviderError(
                            self.provider_name,
                            poll_data.get("error", "Transcription failed"),
                        )

                    await asyncio.sleep(2)

        except httpx.HTTPStatusError as e:
            raise STTProviderError(self.provider_name, f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise STTProviderError(self.provider_name, f"Connection error: {e}")
