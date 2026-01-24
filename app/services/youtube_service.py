"""
YouTube service utilities.
Handles video information retrieval, transcript fetching, and audio download.
"""
import os
import re
import tempfile
import yt_dlp
from typing import Tuple, Optional, Dict, Any, List

from youtube_transcript_api import YouTubeTranscriptApi
from app.utils.logger import logger
from app.services.transcription_service import transcribe_with_whisper
from app.services.gemini_audio_service import transcribe_with_gemini
from app.utils.formatting import format_seconds
from app.utils.decorators import retry
from app.exceptions import AudioDownloadError, ValidationError
from app.config import config
from app.constants import (
    YT_DLP_FORMAT,
    YT_DLP_USER_AGENT,
    YT_DLP_FRAGMENT_RETRIES,
    YT_DLP_SOCKET_TIMEOUT,
    PREFERRED_AUDIO_CODEC,
    PREFERRED_AUDIO_QUALITY,
    MAX_DOWNLOAD_ATTEMPTS,
    DOWNLOAD_RETRY_DELAY,
    COOKIES_FILENAME,
    ERROR_INVALID_URL
)

class YouTubeService:
    """
    Service for handling YouTube-related operations.
    Encapsulates logic for downloading audio, fetching transcripts, and validating videos.
    """

    def get_transcript(self, video_url: str, use_diarization: bool = False) -> Tuple[Optional[str], str]:
        """
        Get transcript for a video, either via YouTube API or Whisper/Gemini fallback.
        
        Args:
            video_url: YouTube URL
            use_diarization: Whether to use Gemini for speaker diarization
            
        Returns:
            Tuple of (transcript_text, source)
        """
        video_id = self.extract_video_id(video_url)
        if not video_id:
            logger.error("Invalid YouTube URL")
            return None, ERROR_INVALID_URL

        # 1. Try YouTube API first (fastest, free) - ONLY if not diarization
        if not use_diarization:
            transcript, source = self._get_youtube_api_transcript(video_id)
            if transcript:
                return transcript, source

        # 2. Fallback to Audio Transcription (Whisper or Gemini)
        return self._transcribe_audio(video_url, use_diarization)

    def get_video_title(self, url: str) -> Optional[str]:
        """Fetch video title using yt-dlp."""
        try:
            ydl_opts = self._get_ydl_options(download_audio=False)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('title')
        except Exception as e:
            logger.error(f"Failed to fetch video title: {e}")
            return None

    def _transcribe_audio(self, video_url: str, use_diarization: bool) -> Tuple[Optional[str], str]:
        """Download audio and transcribe using configured service."""
        audio_path = self._download_audio(video_url)
        if not audio_path:
            return None, "Audio download failed"

        try:
            if use_diarization:
                logger.info("Using Gemini for diarization...")
                title = self.get_video_title(video_url)
                # We could fetch duration here if needed for grounding
                transcript, source = transcribe_with_gemini(audio_path, title=title)
                return transcript, source
            else:
                logger.info("Using Whisper fallback...")
                transcript = transcribe_with_whisper(audio_path)
                return transcript, "whisper" if transcript else "failed"

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None, str(e)
        finally:
            self._cleanup_file(audio_path)

    def _get_youtube_api_transcript(self, video_id: str) -> Tuple[Optional[str], Optional[str]]:
        """Fetch transcript from YouTube Caption API."""
        try:
            logger.info(f"Attempting YouTube transcript API for: {video_id}")
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            try:
                transcript = transcript_list.find_transcript(['en'])
            except Exception:
                transcript = (
                    transcript_list.find_manually_created_transcript() or
                    transcript_list.find_generated_transcript()
                )

            data = transcript.fetch()
            
            # Format: "MM:SS text"
            lines = [f"{format_seconds(item['start'])} {item['text']}" for item in data if item['text'].strip()]
            full_text = '\n'.join(lines)
            
            logger.info(f"[OK] YouTube transcript fetched ({len(full_text)} chars)")
            return full_text, "youtube"

        except Exception as e:
            logger.warning(f"YouTube transcript not available: {e}")
            return None, None

    @retry(max_attempts=MAX_DOWNLOAD_ATTEMPTS, delay=DOWNLOAD_RETRY_DELAY)
    def _download_audio(self, video_url: str) -> Optional[str]:
        """Download audio with retries and duration validation."""
        self._validate_duration(video_url)

        logger.info(f"Downloading audio: {video_url}")
        
        # Secure temp file
        fd, audio_path = tempfile.mkstemp(suffix='.m4a', prefix='yt_audio_')
        os.close(fd)
        
        # Set secure permissions (owner read/write only)
        try:
            os.chmod(audio_path, 0o600)
        except Exception as e:
            logger.warning(f"Could not set file permissions: {e}")
        
        try:
            ydl_opts = self._get_ydl_options(download_audio=True, output_path=audio_path.replace('.m4a', ''))
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # Check for mp3 (post-processed) or original m4a
            mp3_path = audio_path.replace('.m4a', '.mp3')
            if os.path.exists(mp3_path):
                return mp3_path
            if os.path.exists(audio_path): # Should ideally be mp3 due to postprocessor
                return audio_path
                
            raise AudioDownloadError(video_url, "Downloaded file not found")
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            self._cleanup_file(audio_path)
            self._cleanup_file(audio_path.replace('.m4a', '.mp3'))
            raise

    def _validate_duration(self, video_url: str):
        """Ensure video is not too long."""
        try:
            ydl_opts = self._get_ydl_options(download_audio=False)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                duration = info.get('duration', 0)
                
            if duration > config.max_video_duration:
                raise ValidationError(
                    'url', 
                    f"Video too long ({duration/60:.1f}m). Max: {config.max_video_duration/60}m"
                )
        except ValidationError:
            raise
        except Exception as e:
            logger.warning(f"Could not validate duration: {e}")

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract ID from URL."""
        patterns = [r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([\w-]+)']
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _get_ydl_options(self, download_audio: bool = False, output_path: str = None) -> Dict[str, Any]:
        """Configure yt-dlp."""
        options = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': not download_audio
        }

        if download_audio:
            options.update({
                'format': YT_DLP_FORMAT,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': PREFERRED_AUDIO_CODEC,
                    'preferredquality': PREFERRED_AUDIO_QUALITY,
                }],
                'socket_timeout': YT_DLP_SOCKET_TIMEOUT,
                'retries': MAX_DOWNLOAD_ATTEMPTS,
                'fragment_retries': YT_DLP_FRAGMENT_RETRIES,
                'http_headers': {'User-Agent': YT_DLP_USER_AGENT},
            })
            if output_path:
                options['outtmpl'] = output_path

        cookies = self._get_cookies_path()
        if cookies:
            options['cookiefile'] = cookies
            
        return options

    def _get_cookies_path(self) -> Optional[str]:
        """Get path to cookies.txt."""
        path = os.path.join(os.getcwd(), COOKIES_FILENAME)
        return path if os.path.exists(path) else None

    def _cleanup_file(self, path: str):
        """Safely remove a file."""
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
