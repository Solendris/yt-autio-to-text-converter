"""
YouTube service utilities.
Handles video information retrieval, transcript fetching, and audio download.
"""
import os
import re
import tempfile
import yt_dlp
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi

from app.utils.logger import logger
from app.services.transcription_service import transcribe_with_whisper
from app.utils.formatting import format_seconds
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


def get_cookies_path() -> Optional[str]:
    """
    Get path to cookies.txt file if it exists.

    Returns:
        Path to cookies file or None if not found
    """
    cookies_path = os.path.join(os.getcwd(), COOKIES_FILENAME)
    return cookies_path if os.path.exists(cookies_path) else None


def get_ydl_options(
    download_audio: bool = False,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get yt-dlp options with cookies support.

    Args:
        download_audio: Whether to configure for audio download
        output_path: Optional output path for downloads

    Returns:
        Dictionary of yt-dlp options
    """
    options = {
        'quiet': True,
        'no_warnings': True,
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
            'skip_unavailable_fragments': True,
            'http_headers': {
                'User-Agent': YT_DLP_USER_AGENT
            }
        })

        if output_path:
            options['outtmpl'] = output_path
    else:
        options['skip_download'] = True

    # Add cookies if available
    cookies_path = get_cookies_path()
    if cookies_path:
        logger.info(f"Using cookies from: {cookies_path}")
        options['cookiefile'] = cookies_path

    return options


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL.

    Args:
        url: YouTube URL

    Returns:
        Video ID or None if extraction failed
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([\w-]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def get_video_title(url: str) -> Optional[str]:
    """
    Fetch video title using yt-dlp.

    Args:
        url: YouTube URL

    Returns:
        Video title or None if failed
    """
    try:
        ydl_opts = get_ydl_options(download_audio=False)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title', None)

    except Exception as e:
        logger.error(f"Failed to fetch video title: {e}")
        return None


def get_youtube_transcript(video_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch transcript using YouTube Transcript API.

    Args:
        video_id: YouTube video ID

    Returns:
        Tuple of (transcript_text, source) or (None, None) if failed
    """
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

        transcript_data = transcript.fetch()

        # Format with timestamps
        formatted_lines = []
        for item in transcript_data:
            start = item['start']
            text = item['text']
            if text.strip():
                formatted_lines.append(f"{format_seconds(start)} {text}")

        full_text = '\n'.join(formatted_lines)
        logger.info(f"[OK] YouTube transcript fetched ({len(full_text)} characters)")
        return full_text, "youtube"

    except Exception as e:
        logger.warning(f"YouTube transcript not available: {str(e)}")
        return None, None


def download_audio_from_youtube(video_url: str) -> Optional[str]:
    """
    Download audio from YouTube video.
    
    Validates video duration before download to prevent processing
    excessively long videos (High Vulnerability #5).
    
    Refactored to use @retry decorator for DRY compliance.
    
    Args:
        video_url: YouTube URL
        
    Returns:
        Path to downloaded audio file or None if failed
        
    Raises:
        ValidationError: If video is too long
        AudioDownloadError: If download fails
    """
    from app.utils.decorators import retry
    from app.exceptions import AudioDownloadError
    from app.config import config
    
    # First, validate video duration (before downloading)
    logger.info(f"Validating video duration for: {video_url}")
    try:
        ydl_opts = get_ydl_options(download_audio=False)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            duration = info.get('duration', 0)
            
            if duration > config.max_video_duration:
                from app.exceptions import ValidationError
                duration_minutes = duration / 60
                max_minutes = config.max_video_duration / 60
                raise ValidationError(
                    'url',
                    f'Video too long ({duration_minutes:.1f} minutes). '
                    f'Maximum allowed: {max_minutes:.1f} minutes (1.5 hours)'
                )
            
            logger.info(f"Video duration: {duration}s (within limit of {config.max_video_duration}s)")
    except ValidationError:
        raise
    except Exception as e:
        logger.warning(f"Could not validate video duration: {e}")
        # Continue anyway - don't fail on metadata retrieval
    
    @retry(max_attempts=MAX_DOWNLOAD_ATTEMPTS, delay=DOWNLOAD_RETRY_DELAY, backoff=1.0)
    def _download() -> str:
        """Inner function with retry logic."""
        logger.info(f"Downloading audio: {video_url}")
        
        # Use secure temporary file creation
        # Addresses: High Vulnerability #8 - Insecure Temporary Files
        fd, audio_path = tempfile.mkstemp(
            suffix='.m4a',
            prefix='yt_audio_',
            dir=None  # Use secure system temp directory
        )
        os.close(fd)  # Close file descriptor, keep file
        
        # Set secure permissions (owner read/write only)
        try:
            os.chmod(audio_path, 0o600)
        except Exception as e:
            logger.warning(f"Could not set file permissions: {e}")
        
        ydl_opts = get_ydl_options(
            download_audio=True,
            output_path=audio_path.replace('.m4a', '')
        )
        
        logger.info(f"Requested yt-dlp format: {YT_DLP_FORMAT}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # Check for mp3 file (after conversion)
        mp3_path = audio_path.replace('.m4a', '.mp3')
        if os.path.exists(mp3_path):
            logger.info(f"[OK] Audio downloaded: {mp3_path}")
            return mp3_path
        
        raise AudioDownloadError(video_url, "Downloaded audio file not found")
    
    # EAFP: Try to download, handle errors
    try:
        return _download()
    except AudioDownloadError:
        raise
    except Exception as e:
        logger.error(f"Audio download error: {str(e)}")
        raise AudioDownloadError(video_url, str(e))


def get_diarized_transcript(video_url: str) -> Tuple[Optional[str], str]:
    """
    Get transcript with speaker diarization using Gemini Audio.

    Args:
        video_url: YouTube URL

    Returns:
        Tuple of (transcript, source) or (None, error_message)
    """
    from app.services.gemini_audio_service import transcribe_with_gemini

    logger.info(">>> SECTION 1: Getting diarized transcript (Gemini) <<<")

    # Fetch metadata first for better Gemini grounding
    title = get_video_title(video_url)
    
    # Get duration for grounding (using yt-dlp to get detailed info)
    duration_str = "Unknown"
    try:
        ydl_opts = get_ydl_options(download_audio=False)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            duration = info.get('duration')
            if duration:
                duration_str = format_seconds(duration)
    except Exception as e:
        logger.warning(f"Could not fetch video duration: {e}")

    audio_path = download_audio_from_youtube(video_url)
    if not audio_path:
        return None, "Audio download failed"

    try:
        transcript, source = transcribe_with_gemini(
            audio_path, 
            title=title, 
            duration=duration_str
        )
        return transcript, source

    except Exception as e:
        logger.error(f"Diarized transcription failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None, str(e)

    finally:
        # Cleanup audio file - Always run (Fix for Local File Leak)
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                logger.info(f"[CLEANUP] Deleted temp audio: {audio_path}")
            except Exception as cleanup_e:
                logger.warning(f"Failed to clean up audio file: {cleanup_e}")


def get_transcript(video_url: str) -> Tuple[Optional[str], str]:
    """
    Get transcript using YouTube API or Whisper fallback.

    Args:
        video_url: YouTube URL

    Returns:
        Tuple of (transcript, source) or (None, error_message)
    """
    video_id = extract_video_id(video_url)
    if not video_id:
        logger.error("Invalid YouTube URL")
        return None, ERROR_INVALID_URL

    logger.info(">>> SECTION 1: Getting transcript <<<")

    # Try YouTube transcript first
    transcript, source = get_youtube_transcript(video_id)
    if transcript:
        logger.info("Using YouTube transcript source")
        return transcript, source

    # Fallback to Whisper
    logger.info("Falling back to Whisper...")
    audio_path = download_audio_from_youtube(video_url)
    if not audio_path:
        logger.error("Audio download failed")
        return None, "Failed to download audio"

    try:
        transcript = transcribe_with_whisper(audio_path)

        if transcript:
            logger.info("Using Whisper transcript source")
            return transcript, "whisper"
            
        logger.error("Whisper returned empty transcript")
        return None, "Failed to transcribe audio (Empty)"

    except Exception as e:
        logger.error(f"Whisper transcription failed: {str(e)}")
        return None, f"Whisper failed: {str(e)}"

    finally:
        # Cleanup - Always run (Fix for Local File Leak)
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                logger.info(f"[CLEANUP] Deleted temp audio: {audio_path}")
            except Exception as cleanup_e:
                logger.warning(f"Failed to clean up audio file: {cleanup_e}")
