"""
Controllers for handling business logic.

Controllers implement the orchestration layer between routes and services,
following these principles:
- SRP: Each controller handles one domain area
- TDA: Tell services what to do, don't ask then decide
- DIP: Depend on abstractions (future: interfaces)
- SoC: Separate HTTP concerns from business logic
"""

from typing import Tuple, Optional, Dict, Any
from app.utils.logger import logger
from app.exceptions import TranscriptError, ValidationError
from app.models import TranscriptRequest, TranscriptResponse


class TranscriptController:
    """
    Controller for transcript-related operations.
    
    This controller encapsulates all business logic for transcript generation,
    keeping routes thin and focused on HTTP handling.
    
    Principles applied:
    - SRP: Only handles transcript operations
    - TDA: Tells services what to do
    - Clean separation from Flask
    """
    
    def __init__(self):
        """Initialize controller with service dependencies."""
        # Future: Inject services via constructor (DIP)
        # For now, import directly
        from app.services.youtube_service import (
            get_transcript,
            get_diarized_transcript
        )
        from app.constants import SUCCESS_TRANSCRIPT_READY
        
        self._get_transcript = get_transcript
        self._get_diarized_transcript = get_diarized_transcript
        self._success_message = SUCCESS_TRANSCRIPT_READY
    
    def generate_transcript(
        self,
        request_data: TranscriptRequest
    ) -> TranscriptResponse:
        """
        Generate transcript from video URL.
        
        This method implements TDA (Tell, Don't Ask):
        - Routes tell this method to generate transcript
        - This method tells services to fetch transcript
        - No asking "did it work?" and deciding
        
        Args:
            request_data: Validated transcript request
            
        Returns:
            TranscriptResponse with transcript data
            
        Raises:
            TranscriptError: If transcript generation fails
        """
        logger.info(
            f"Processing transcript request: {request_data.url} "
            f"(Diarization: {request_data.diarization})"
        )
        
        # Tell service to get transcript (TDA)
        if request_data.diarization:
            transcript, source = self._get_diarized_transcript(request_data.url)
        else:
            transcript, source = self._get_transcript(request_data.url)
        
        # Fail Fast: No transcript = error
        if not transcript:
            raise TranscriptError(
                source or "Transcript generation failed",
                source
            )
        
        logger.info(f"[OK] {self._success_message} - source: {source}")
        
        # Build response
        return TranscriptResponse(
            transcript=transcript,
            source=source,
            filename=f'transcript_{request_data.video_id}_{source}.txt',
            video_id=request_data.video_id
        )
    
    def validate_transcript_file(
        self,
        file_content: str,
        filename: str
    ) -> Dict[str, Any]:
        """
        Validate uploaded transcript file.
        
        Args:
            file_content: Content of the uploaded file
            filename: Name of the file
            
        Returns:
            Dictionary with validation results
        """
        logger.info(f"Validating file: {filename}")
        
        file_size = len(file_content)
        word_count = len(file_content.split())
        
        logger.info(f"[OK] File validated")
        logger.info(f"[STATS] Size: {file_size} characters | Words: {word_count}")
        
        preview = file_content[:200] + '...' if len(file_content) > 200 else file_content
        
        return {
            'filename': filename,
            'size': file_size,
            'words': word_count,
            'preview': preview
        }


class SummaryController:
    """
    Controller for summarization operations.
    
    Handles both URL-based and file-based summarization.
    """
    
    def __init__(self):
        """Initialize controller with service dependencies."""
        from app.services.youtube_service import get_transcript, extract_video_id, get_video_title
        from app.services.summarization_service import summarize_with_perplexity, summarize_with_gemini
        from app.config import config
        
        self._get_transcript = get_transcript
        self._extract_video_id = extract_video_id
        self._get_video_title = get_video_title
        self._summarize_perplexity = summarize_with_perplexity
        self._summarize_gemini = summarize_with_gemini
        self._config = config
    
    def generate_summary(
        self,
        transcript: str,
        summary_type: str
    ) -> str:
        """
        Generate summary from transcript.
        
        Implements TDA: Tell summarization service to summarize,
        don't ask which provider then decide.
        
        Args:
            transcript: Text to summarize
            summary_type: Type of summary ('concise', 'normal', 'detailed')
            
        Returns:
            Summary text
            
        Raises:
            SummarizationError: If all providers fail
        """
        from app.exceptions import SummarizationError
        
        logger.info(f"[START] Summarization process ({summary_type} mode)")
        
        summary = None
        
        # Try primary provider
        if self._config.use_perplexity:
            logger.info("Using Perplexity API...")
            summary = self._summarize_perplexity(transcript, summary_type)
            
            # Fallback to Gemini if Perplexity fails
            if not summary and self._config.google_api_key:
                logger.warning("Perplexity failed, trying Gemini...")
                summary = self._summarize_gemini(transcript, summary_type)
        else:
            logger.info("Using Gemini API...")
            summary = self._summarize_gemini(transcript, summary_type)
        
        # Fail Fast: No summary = error
        if not summary:
            raise SummarizationError(
                self._config.ai_provider,
                "All summarization APIs failed"
            )
        
        logger.info(f"[OK] Summary generated ({len(summary)} characters)")
        return summary
    
    def get_transcript_for_url(
        self,
        video_url: str
    ) -> Tuple[str, str, str, str]:
        """
        Get transcript and metadata from video URL.
        
        Args:
            video_url: YouTube URL
            
        Returns:
            Tuple of (transcript, source, video_id, title)
            
        Raises:
            TranscriptError: If transcript retrieval fails
        """
        transcript, source = self._get_transcript(video_url)
        
        if not transcript:
            raise TranscriptError(
                source or "Transcript generation failed",
                source
            )
        
        video_id = self._extract_video_id(video_url)
        title = self._get_video_title(video_url) or f'Video {video_id}'
        
        logger.info(f"Transcript ready ({len(transcript)} chars)")
        
        return transcript, source, video_id, title


class HealthController:
    """
    Controller for health check operations.
    
    Simple controller for system status.
    """
    
    def __init__(self):
        """Initialize controller."""
        from app.config import config
        self._config = config
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get application health status.
        
        Returns:
            Dictionary with health information
        """
        from app.models import HealthResponse
        
        logger.debug("Health check")
        
        response = HealthResponse(
            version='2.0.0',
            sections=['transcript', 'summarize'],
            perplexity_configured=self._config.use_perplexity,
            gemini_configured=bool(self._config.google_api_key),
            ai_provider=self._config.ai_provider
        )
        
        return response.to_dict()
