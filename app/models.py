"""
Request and response data models.

These models provide:
- Type safety and validation
- Self-documenting API contracts
- Fail Fast validation (errors caught early)
- Convention over Configuration (dataclass boilerplate)
"""

from dataclasses import dataclass, field
from typing import Optional
from app.exceptions import ValidationError


@dataclass
class TranscriptRequest:
    """
    Request model for transcript generation.
    
    Validates and normalizes transcript request data.
    Implements Fail Fast by validating in __post_init__.
    """
    
    url: str
    diarization: bool = False
    
    def __post_init__(self):
        """
        Validate request data immediately after initialization.
        
        This implements the Fail Fast principle - invalid data
        is rejected immediately rather than causing errors later.
        
        Raises:
            ValidationError: If URL is invalid or empty
        """
        # Normalize URL
        self.url = self.url.strip()
        
        # Fail Fast validation
        if not self.url:
            raise ValidationError('url', 'URL is required')
        
        # Validate URL format
        from app.validators import validate_youtube_url
        is_valid, error_msg = validate_youtube_url(self.url)
        if not is_valid:
            raise ValidationError('url', error_msg)
    
    @property
    def video_id(self) -> Optional[str]:
        """
        Extract video ID from URL.
        
        This implements Law of Demeter - external code doesn't need
        to know how to extract the ID, they just ask for it.
        """
        from app.services.youtube_service import extract_video_id
        return extract_video_id(self.url)


@dataclass
class SummarizeRequest:
    """
    Request model for summarization.
    
    Supports both URL-based and file upload-based summarization.
    """
    
    url: Optional[str] = None
    summary_type: str = 'normal'
    output_format: str = 'pdf'
    transcript_text: Optional[str] = None
    filename: Optional[str] = None
    
    def __post_init__(self):
        """Validate and normalize request data."""
        # Normalize summary type
        from app.validators import validate_summary_type, validate_output_format
        self.summary_type = validate_summary_type(self.summary_type)
        self.output_format = validate_output_format(self.output_format)
        
        # Validate that we have either URL or transcript
        if not self.url and not self.transcript_text:
            raise ValidationError(
                'request',
                'Either URL or transcript text must be provided'
            )
        
        # If URL provided, validate it
        if self.url:
            self.url = self.url.strip()
            from app.validators import validate_youtube_url
            is_valid, error_msg = validate_youtube_url(self.url)
            if not is_valid:
                raise ValidationError('url', error_msg)
    
    @property
    def video_id(self) -> str:
        """Extract video ID or return default for file uploads."""
        if self.url:
            from app.services.youtube_service import extract_video_id
            return extract_video_id(self.url) or 'unknown'
        return 'manual_upload'
    
    @property
    def is_file_upload(self) -> bool:
        """Check if this is a file upload request."""
        return self.transcript_text is not None and not self.url


@dataclass
class HybridRequest:
    """Request model for hybrid PDF generation (summary + transcript)."""
    
    url: str
    summary_type: str = 'normal'
    title: Optional[str] = None
    
    def __post_init__(self):
        """Validate request data."""
        self.url = self.url.strip()
        
        if not self.url:
            raise ValidationError('url', 'URL is required')
        
        from app.validators import validate_youtube_url, validate_summary_type
        is_valid, error_msg = validate_youtube_url(self.url)
        if not is_valid:
            raise ValidationError('url', error_msg)
        
        self.summary_type = validate_summary_type(self.summary_type)
    
    @property
    def video_id(self) -> Optional[str]:
        """Extract video ID from URL."""
        from app.services.youtube_service import extract_video_id
        return extract_video_id(self.url)


@dataclass
class TranscriptResponse:
    """
    Response model for transcript generation.
    
    Provides structured data for transcript responses.
    """
    
    transcript: str
    source: str
    filename: str
    video_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'transcript': self.transcript,
            'source': self.source,
            'filename': self.filename,
            'video_id': self.video_id
        }


@dataclass
class HealthResponse:
    """Response model for health check endpoint."""
    
    version: str
    sections: list
    perplexity_configured: bool
    gemini_configured: bool
    ai_provider: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'version': self.version,
            'sections': self.sections,
            'perplexity_configured': self.perplexity_configured,
            'gemini_configured': self.gemini_configured,
            'ai_provider': self.ai_provider
        }


@dataclass
class ValidationErrorResponse:
    """Response model for validation errors."""
    
    field: str
    message: str
    code: str = 'validation_error'
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'code': self.code,
            'field': self.field,
            'message': self.message
        }
