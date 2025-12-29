"""
YouTube service utilities.
Handles video information retrieval, transcript fetching, and audio download.
"""
import os
import re
import tempfile
import yt_dlp
import shutil
import subprocess
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi

import base64
from app.config import Config
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
    ERROR_INVALID_URL,
    COOKIES_FILENAME
)


class YdlLogger:
    """Custom logger to capture yt-dlp internal messages."""
    def debug(self, msg):
        if msg.startswith('[debug] '):
            logger.debug(msg)
        else:
            self.info(msg)

    def info(self, msg):
        logger.info(msg)

    def warning(self, msg):
        logger.warning(msg)

    def error(self, msg):
        logger.error(msg)


def get_ydl_options(
    download_audio: bool = False,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get yt-dlp options with TV client impersonation and robust cookies support.
    Prioritizes physical cookies.txt (Render Secret File) over YOUTUBE_COOKIES_B64.

    Args:
        download_audio: Whether to configure for audio download
        output_path: Optional output path for downloads

    Returns:
        Dictionary of yt-dlp options
    """
    options = {
        'logger': YdlLogger(),
        'verbose': True,  # Added for maximum transparency in logs
        'quiet': False,   # Set to False to see what's happening
        'no_warnings': False,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'force_ipv4': True,
        'no_cache_dir': True, # Important: force fresh JS solvers
    }

    # 1. Priority: Physical cookies.txt (local or Render Secret File)
    cookies_path = os.path.join(os.getcwd(), COOKIES_FILENAME)
    if os.path.exists(cookies_path):
        logger.info(f"Using physical cookies file at: {cookies_path}")
        options['cookiefile'] = cookies_path
    
    # 2. Fallback: Base64 Env Var (if no physical file and var exists)
    elif Config.YOUTUBE_COOKIES_B64:
        try:
            decoded_cookies = base64.b64decode(Config.YOUTUBE_COOKIES_B64).decode('utf-8')
            cookie_file_path = os.path.join(tempfile.gettempdir(), f"yt_cookies_{os.getpid()}.txt")
            with open(cookie_file_path, 'w', encoding='utf-8') as f:
                f.write(decoded_cookies)
            logger.info(f"Using ephemeral cookies from B64 env var at: {cookie_file_path}")
            options['cookiefile'] = cookie_file_path
        except Exception as e:
            logger.error(f"Failed to decode YOUTUBE_COOKIES_B64: {str(e)}")

    if download_audio:
        # Check if FFmpeg is available
        ffmpeg_available = shutil.which('ffmpeg') is not None
        if not ffmpeg_available:
            logger.warning("FFmpeg NOT found! Disabling audio conversion post-processing. Downloading raw audio.")
        
        # 'bestaudio/best' is broad: it takes the best audio-only stream.
        options.update({
            'format': 'bestaudio/best',
            'format_sort': ['acodec:aac', 'ext:m4a', 'abr', 'quality'],
            'socket_timeout': YT_DLP_SOCKET_TIMEOUT,
            'retries': MAX_DOWNLOAD_ATTEMPTS,
            'fragment_retries': YT_DLP_FRAGMENT_RETRIES,
            'skip_unavailable_fragments': True,
        })

        # Smart Client Selection
        # If cookies are provided, Android/iOS clients are invalid (they don't support cookies).
        # We prioritize 'web' as it's the native environment for browser cookies,
        # but keep 'tv' as it often bypasses SABR forcing.
        if options.get('cookiefile'):
             options['extractor_args'] = {
                'youtube': {
                    'player_client': ['web', 'tv'],
                    'include_dash_manifest': True,
                    'include_hls_manifest': True,
                }
            }
        else:
            # No cookies? Use mobile + tv clients to bypass initial blocks
            options['extractor_args'] = {
                'youtube': {
                    'player_client': ['android', 'ios', 'tv', 'web'],
                }
            }
        
        # Check formats and handle SABR-related issues
        options.update({
            'check_formats': True,
            'prefer_free_formats': False, # Sometimes True helps, but let's stick to False for quality
            'youtube_include_dash_manifest': True,
            'youtube_include_hls_manifest': True,
        })

        # Only add FFmpeg postprocessor if FFmpeg is actually present
        if ffmpeg_available:
            options['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': PREFERRED_AUDIO_CODEC,
                'preferredquality': PREFERRED_AUDIO_QUALITY,
            }]

        if output_path:
            options['outtmpl'] = output_path
    else:
        options['skip_download'] = True

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

    Args:
        video_url: YouTube URL

    Returns:
        Path to downloaded audio file or None if failed
    """
    try:
        logger.info(f"Downloading audio: {video_url}")

        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        audio_path = os.path.join(temp_dir, f"yt_audio_{timestamp}.m4a")

        ydl_opts = get_ydl_options(
            download_audio=True,
            output_path=audio_path.replace('.m4a', '')
        )
        
        # Log environment state for debugging Render
        logger.info(f"--- Environment Debug ---")
        logger.info(f"Current Working Directory: {os.getcwd()}")
        logger.info(f"FFmpeg path: {shutil.which('ffmpeg')}")
        logger.info(f"YT-DLP Format: {ydl_opts.get('format')}")
        if ydl_opts.get('cookiefile'):
            exists = os.path.exists(ydl_opts['cookiefile'])
            logger.info(f"Cookies file exists at path: {exists}")
            if exists:
                try:
                    with open(ydl_opts['cookiefile'], 'r') as f:
                        header = f.readline()
                        logger.info(f"Cookie file header: {header.strip()[:50]}")
                except Exception as e:
                    logger.error(f"Failed to read cookie file: {e}")
        
        node_path = shutil.which('node') or shutil.which('nodejs')
        logger.info(f"Node.js path: {node_path}")
        if node_path:
            try:
                # Test if we can actually run it
                node_test = subprocess.run([node_path, '-e', 'console.log("JS OK")'], capture_output=True, text=True, timeout=5)
                logger.info(f"Node.js test execution: {node_test.stdout.strip()} (Return code: {node_test.returncode})")
                node_version = subprocess.check_output([node_path, '--version']).decode().strip()
                logger.info(f"Node.js version: {node_version}")
            except Exception as e:
                logger.error(f"Node.js found but FAILING TO RUN: {e}")
        else:
            logger.error("CRITICAL: Node.js NOT FOUND in path! Check Docker build logs.")
        
        # Log system PATH to see where things are
        logger.info(f"System PATH: {os.environ.get('PATH')}")
        logger.info(f"--------------------------")

        logger.info(f"Requested yt-dlp format: {YT_DLP_FORMAT}")

        # Retry logic
        for attempt in range(1, MAX_DOWNLOAD_ATTEMPTS + 1):
            try:
                logger.info(f"Audio download attempt {attempt}/{MAX_DOWNLOAD_ATTEMPTS}...")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                break
            except Exception as e:
                if attempt == MAX_DOWNLOAD_ATTEMPTS:
                    raise
                logger.warning(f"Attempt {attempt} failed ({str(e)}), retrying...")
                import time
                time.sleep(DOWNLOAD_RETRY_DELAY)

        mp3_path = audio_path.replace('.m4a', '.mp3')
        if os.path.exists(mp3_path):
            logger.info(f"[OK] Audio downloaded: {mp3_path}")
            return mp3_path

        logger.error("Downloaded audio file not found")
        return None

    except Exception as e:
        logger.error(f"Audio download error: {str(e)}")
        return None


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

    audio_path = download_audio_from_youtube(video_url)
    if not audio_path:
        return None, "Audio download failed"

    try:
        transcript, source = transcribe_with_gemini(audio_path)

        # Cleanup audio file
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception as cleanup_e:
                logger.warning(f"Failed to clean up audio file: {cleanup_e}")

        return transcript, source

    except Exception as e:
        logger.error(f"Diarized transcription failed: {str(e)}")
        return None, str(e)


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

        # Cleanup
        if os.path.exists(audio_path):
            os.remove(audio_path)

        if transcript:
            logger.info("Using Whisper transcript source")
            return transcript, "whisper"

    except Exception as e:
        logger.error(f"Whisper transcription failed: {str(e)}")

    logger.error("Both YouTube and Whisper failed")
    return None, "Failed to transcribe audio"
