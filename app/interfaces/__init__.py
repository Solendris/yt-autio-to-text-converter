"""
Abstract interfaces for services.

Defines abstract base classes (ABCs) for dependency inversion principle (DIP).
Services depend on these abstractions rather than concrete implementations.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional


class TranscriptProvider(ABC):
    """
    Abstract interface for transcript providers.
    
    This implements the Dependency Inversion Principle:
    - High-level modules (routes, controllers) depend on this abstraction
    - Low-level modules (YouTube API, Whisper) implement this interface
    
    Benefits:
    - Easy to swap implementations
    - Easy to mock for testing
    - Clear contract for all providers
    """
    
    @abstractmethod
    def get_transcript(self, video_url: str) -> Tuple[str, str]:
        """
        Get transcript from video URL.
        
        Args:
            video_url: URL of the video
            
        Returns:
            Tuple of (transcript_text, source_name)
            
        Raises:
            TranscriptError: If transcript generation fails
        """
        pass
    
    @abstractmethod
    def supports_diarization(self) -> bool:
        """
        Check if this provider supports speaker diarization.
        
        Returns:
            True if diarization is supported
        """
        pass


class Summarizer(ABC):
    """
    Abstract interface for text summarization providers.
    
    Allows swapping between Gemini, Perplexity, or other AI services.
    """
    
    @abstractmethod
    def summarize(
        self,
        text: str,
        summary_type: str = 'normal'
    ) -> str:
        """
        Summarize the given text.
        
        Args:
            text: Text to summarize
            summary_type: Type of summary ('concise', 'normal', 'detailed')
            
        Returns:
            Summarized text
            
        Raises:
            SummarizationError: If summarization fails
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of this summarization provider.
        
        Returns:
            Provider name (e.g., 'gemini', 'perplexity')
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this provider is properly configured and available.
        
        Returns:
            True if provider can be used
        """
        pass


class AudioDownloader(ABC):
    """
    Abstract interface for audio download services.
    
    Allows different implementations (yt-dlp, youtube-dl, etc.)
    """
    
    @abstractmethod
    def download(self, video_url: str) -> str:
        """
        Download audio from video URL.
        
        Args:
            video_url: URL of the video
            
        Returns:
            Path to downloaded audio file
            
        Raises:
            AudioDownloadError: If download fails
        """
        pass
    
    @abstractmethod
    def cleanup(self, file_path: str) -> None:
        """
        Clean up downloaded audio file.
        
        Args:
            file_path: Path to file to clean up
        """
        pass


class Transcriber(ABC):
    """
    Abstract interface for audio transcription services.
    
    Allows different implementations (Whisper, Gemini Audio, etc.)
    """
    
    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            language: Optional language code (e.g., 'en')
            
        Returns:
            Tuple of (transcript_text, source_name)
            
        Raises:
            TranscriptionServiceError: If transcription fails
        """
        pass
    
    @abstractmethod
    def supports_diarization(self) -> bool:
        """
        Check if this transcriber supports speaker diarization.
        
        Returns:
            True if diarization is supported
        """
        pass


class PDFGenerator(ABC):
    """
    Abstract interface for PDF generation services.
    
    Allows different PDF libraries (ReportLab, FPDF, etc.)
    """
    
    @abstractmethod
    def create_summary_pdf(
        self,
        title: str,
        content: str,
        metadata: dict
    ) -> bytes:
        """
        Create a PDF with summary content.
        
        Args:
            title: Document title
            content: Summary content
            metadata: Additional metadata
            
        Returns:
            PDF file as bytes
        """
        pass
    
    @abstractmethod
    def create_hybrid_pdf(
        self,
        title: str,
        summary: str,
        transcript: str,
        metadata: dict
    ) -> bytes:
        """
        Create a PDF with both summary and transcript.
        
        Args:
            title: Document title
            summary: Summary content
            transcript: Full transcript
            metadata: Additional metadata
            
        Returns:
            PDF file as bytes
        """
        pass
