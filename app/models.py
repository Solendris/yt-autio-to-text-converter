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
    gemini_configured: bool
    ai_provider: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'version': self.version,
            'sections': self.sections,
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
