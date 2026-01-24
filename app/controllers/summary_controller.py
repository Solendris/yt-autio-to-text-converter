"""
Controller for summarization operations.
"""
from typing import Tuple
from app.services.youtube_service import YouTubeService
from app.services.summarization_service import SummarizationService
from app.services.pdf_service import create_pdf_summary, create_hybrid_pdf
from app.exceptions import SummarizationError, TranscriptError
from app.utils.logger import logger
from app.config import config

class SummaryController:
    def __init__(self):
        self.youtube_service = YouTubeService()
        self.summary_service = SummarizationService()

    def generate_summary(self, transcript: str, summary_type: str) -> str:
        """Generate summary from transcript."""
        logger.info(f"[START] Summarization process ({summary_type} mode)")
        
        summary = self.summary_service.summarize(transcript, summary_type)
        
        if not summary:
            raise SummarizationError(config.ai_provider, "All summarization APIs failed")
            
        logger.info(f"[OK] Summary generated ({len(summary)} characters)")
        return summary

    def get_transcript_for_url(self, video_url: str) -> Tuple[str, str, str, str]:
        """Get transcript and metadata from video URL."""
        transcript, source = self.youtube_service.get_transcript(video_url)
        
        if not transcript:
            raise TranscriptError(source or "Transcript generation failed", source)
            
        video_id = self.youtube_service.extract_video_id(video_url)
        title = self.youtube_service.get_video_title(video_url) or f'Video {video_id}'
        
        return transcript, source, video_id, title

    def create_pdf(self, title: str, summary: str, url: str, source: str, summary_type: str):
        return create_pdf_summary(title, summary, url, source, summary_type)

    def create_hybrid_pdf(self, title: str, summary: str, transcript: str, url: str, source: str, summary_type: str):
        return create_hybrid_pdf(title, summary, transcript, url, source, summary_type)
