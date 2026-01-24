"""
Controller for transcript operations.
"""
from typing import Dict, Any
from app.services.youtube_service import YouTubeService
from app.models import TranscriptRequest, TranscriptResponse
from app.exceptions import TranscriptError
from app.utils.logger import logger
from app.constants import SUCCESS_TRANSCRIPT_READY

class TranscriptController:
    def __init__(self):
        self.youtube_service = YouTubeService()

    def generate_transcript(self, request_data: TranscriptRequest) -> TranscriptResponse:
        """
        Generate transcript from video URL.
        """
        logger.info(f"Processing transcript request: {request_data.url} (Diarization: {request_data.diarization})")
        
        transcript, source = self.youtube_service.get_transcript(
            request_data.url, 
            use_diarization=request_data.diarization
        )
        
        if not transcript:
            raise TranscriptError(source or "Transcript generation failed", source)
        
        return TranscriptResponse(
            transcript=transcript,
            source=source,
            filename=f'transcript_{request_data.video_id}_{source}.txt',
            video_id=request_data.video_id
        )

    def validate_transcript_file(self, file_content: str, filename: str) -> Dict[str, Any]:
        """Validate uploaded transcript file."""
        logger.info(f"Validating file: {filename}")
        
        file_size = len(file_content)
        word_count = len(file_content.split())
        preview = file_content[:200] + '...' if len(file_content) > 200 else file_content
        
        return {
            'filename': filename,
            'size': file_size,
            'words': word_count,
            'preview': preview
        }
