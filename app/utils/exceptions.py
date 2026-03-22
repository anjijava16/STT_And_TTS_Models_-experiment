from fastapi import HTTPException, status


class STTProviderError(HTTPException):
    def __init__(self, provider: str, detail: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"STT provider '{provider}' error: {detail}",
        )


class TTSProviderError(HTTPException):
    def __init__(self, provider: str, detail: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"TTS provider '{provider}' error: {detail}",
        )


class UnsupportedProviderError(HTTPException):
    def __init__(self, provider_type: str, provider: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported {provider_type} provider: '{provider}'",
        )


class AudioFileError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Audio file error: {detail}",
        )


class MissingAPIKeyError(HTTPException):
    def __init__(self, provider: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API key not configured for provider: '{provider}'",
        )
