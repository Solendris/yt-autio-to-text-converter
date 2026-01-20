"""
Custom exception hierarchy for the application.

This module defines a structured exception hierarchy that enables:
- Fail Fast principle: Errors are caught and handled appropriately
- EAFP (Easier to Ask for Forgiveness than Permission): Pythonic error handling
- Clear error categories for better debugging and logging
"""


class AppException(Exception):
    """
    Base exception for all application errors.
    
    All custom exceptions should inherit from this class to enable
    consistent error handling and logging.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code for API responses
        details: Optional additional error information
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ValidationError(AppException):
    """
    Raised when input validation fails.
    
    Examples:
        - Invalid YouTube URL
        - Missing required field
        - Invalid file format
    """
    
    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Validation error on '{field}': {message}",
            status_code=400,
            details={'field': field, 'validation_message': message}
        )
        self.field = field


class ConfigurationError(AppException):
    """
    Raised when application configuration is invalid.
    
    This implements the Fail Fast principle - application should not
    start with invalid configuration.
    
    Examples:
        - Missing required API keys
        - Invalid timeout values
        - Conflicting settings
    """
    
    def __init__(self, message: str):
        super().__init__(
            message=f"Configuration error: {message}",
            status_code=500
        )


class TranscriptError(AppException):
    """
    Raised when transcript generation fails.
    
    This can occur due to:
        - YouTube API failure
        - Audio download failure
        - Transcription service failure
    """
    
    def __init__(self, message: str, source: str = None):
        details = {'source': source} if source else {}
        super().__init__(
            message=f"Transcript error: {message}",
            status_code=500,
            details=details
        )
        self.source = source


class AudioDownloadError(TranscriptError):
    """Raised when audio download fails."""
    
    def __init__(self, url: str, reason: str):
        super().__init__(
            message=f"Failed to download audio from {url}: {reason}",
            source="audio_download"
        )
        self.url = url


class TranscriptionServiceError(TranscriptError):
    """Raised when transcription service (Whisper, Gemini) fails."""
    
    def __init__(self, service_name: str, reason: str):
        super().__init__(
            message=f"{service_name} transcription failed: {reason}",
            source=service_name.lower()
        )
        self.service_name = service_name


class SummarizationError(AppException):
    """
    Raised when text summarization fails.
    
    This can occur due to:
        - API timeout
        - API rate limits
        - Invalid response format
    """
    
    def __init__(self, provider: str, message: str):
        super().__init__(
            message=f"Summarization error ({provider}): {message}",
            status_code=500,
            details={'provider': provider}
        )
        self.provider = provider


class FileProcessingError(AppException):
    """
    Raised when file operations fail.
    
    Examples:
        - File too large
        - Invalid file format
        - File read/write errors
    """
    
    def __init__(self, filename: str, message: str):
        super().__init__(
            message=f"File processing error ({filename}): {message}",
            status_code=400,
            details={'filename': filename}
        )
        self.filename = filename


class ExternalServiceError(AppException):
    """
    Raised when external service calls fail.
    
    This is a generic exception for third-party service failures.
    Use more specific exceptions when available.
    """
    
    def __init__(self, service_name: str, message: str, status_code: int = 503):
        super().__init__(
            message=f"{service_name} service error: {message}",
            status_code=status_code,
            details={'service': service_name}
        )
        self.service_name = service_name


class ResourceNotFoundError(AppException):
    """
    Raised when a requested resource is not found.
    
    Examples:
        - Video not found
        - Transcript not available
        - File not found
    """
    
    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            message=f"{resource_type} not found: {identifier}",
            status_code=404,
            details={'resource_type': resource_type, 'identifier': identifier}
        )
        self.resource_type = resource_type
        self.identifier = identifier
