import os
import re
import tempfile
import yt_dlp
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from app.utils.logger import logger
from app.services.transcription_service import transcribe_with_whisper
from app.utils.formatting import format_seconds

def extract_video_id(url):
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&?\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_title(url):
    try:
        ydl_opts = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title', None)
    except Exception as e:
        logger.error(f"Failed to fetch video title: {e}")
        return None

def get_youtube_transcript(video_id):
    try:
        logger.info(f"Attempting YouTube transcript API for: {video_id}")
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        try:
            transcript = transcript_list.find_transcript(['en'])
        except:
            transcript = transcript_list.find_manually_created_transcript() or transcript_list.find_generated_transcript()
        
        transcript_data = transcript.fetch()
        
        # Format with timestamps
        formatted_lines = []
        for item in transcript_data:
            start = item['start']
            text = item['text']
            # Only add timestamp if text is not empty
            if text.strip():
                formatted_lines.append(f"{format_seconds(start)} {text}")
        
        full_text = '\n'.join(formatted_lines)
        logger.info(f"[OK] YouTube transcript fetched ({len(full_text)} characters)")
        return full_text, "youtube"
    
    except Exception as e:
        logger.warning(f"YouTube transcript not available: {str(e)}")
        return None, None

def download_audio_from_youtube(video_url):
    try:
        logger.info(f"Downloading audio: {video_url}")
        
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"yt_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.m4a")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'outtmpl': audio_path.replace('.m4a', ''),
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 60,
            'retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }
        
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Audio download attempt {attempt}/{max_attempts}...")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                break
            except Exception as e:
                if attempt == max_attempts:
                    raise
                logger.warning(f"Attempt {attempt} failed, retrying...")
                import time
                time.sleep(5)
        
        mp3_path = audio_path.replace('.m4a', '.mp3')
        if os.path.exists(mp3_path):
            logger.info(f"[OK] Audio downloaded: {mp3_path}")
            return mp3_path
        
        logger.error("Downloaded audio file not found")
        return None
    
    except Exception as e:
        logger.error(f"Audio download error: {str(e)}")
        return None

def get_transcript(video_url):
    """SEKCJA 1: Pobierz transkrypt (YouTube API lub Whisper)"""
    video_id = extract_video_id(video_url)
    if not video_id:
        logger.error("Invalid YouTube URL")
        return None, "Invalid YouTube URL"
    
    logger.info(">>> SECTION 1: Getting transcript <<<")
    
    transcript, source = get_youtube_transcript(video_id)
    if transcript:
        logger.info(f"Using YouTube transcript source")
        return transcript, source
    
    logger.info("Falling back to Whisper...")
    audio_path = download_audio_from_youtube(video_url)
    if not audio_path:
        logger.error("Audio download failed")
        return None, "Failed to download audio"
    
    transcript = transcribe_with_whisper(audio_path)
    if transcript:
        logger.info(f"Using Whisper transcript source")
        return transcript, "whisper"
    
    logger.error("Both YouTube and Whisper failed")
    return None, "Failed to transcribe audio"
