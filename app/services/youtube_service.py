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
        
        # Check for cookies.txt
        cookies_path = os.path.join(os.getcwd(), 'cookies.txt')
        if os.path.exists(cookies_path):
            logger.info(f"Using cookies from: {cookies_path}")
            ydl_opts['cookiefile'] = cookies_path
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Log all available formats (equivalent to --list-formats)
            formats = info.get('formats', [])
            logger.info(f"--- AVAILABLE FORMATS for {url} ---")
            for f in formats:
                f_id = f.get('format_id')
                ext = f.get('ext')
                res = f.get('resolution')
                note = f.get('format_note')
                vcodec = f.get('vcodec')
                acodec = f.get('acodec')
                logger.info(f"ID: {f_id} | Ext: {ext} | Res: {res} | V: {vcodec} | A: {acodec} | {note}")
            logger.info("------------------------------------------")
            
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
        
        logger.info(f"Requested yt-dlp format: {ydl_opts['format']}")
        
        # Check for cookies.txt
        cookies_path = os.path.join(os.getcwd(), 'cookies.txt')
        if os.path.exists(cookies_path):
            logger.info(f"Using cookies for download from: {cookies_path}")
            ydl_opts['cookiefile'] = cookies_path
        
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

def get_diarized_transcript(video_url):
    """Pobierz transkrypt z rozpoznawaniem mowców (Gemini Audio)"""
    from app.services.gemini_audio_service import transcribe_with_gemini
    
    logger.info(">>> SECTION 1: Getting diarized transcript (Gemini) <<<")
    
    audio_path = download_audio_from_youtube(video_url)
    if not audio_path:
        return None, "Audio download failed"
        
    try:
        transcript, source = transcribe_with_gemini(audio_path)
        # Clean up audio
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception as cleanup_e:
                logger.warning(f"Failed to clean up audio file {audio_path}: {cleanup_e}")
        return transcript, source
    except Exception as e:
        logger.error(f"Diarized transcription failed: {str(e)}")
        return None, str(e)

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
    
    try:
        transcript = transcribe_with_whisper(audio_path)
        # Cleanup
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
        if transcript:
            logger.info(f"Using Whisper transcript source")
            return transcript, "whisper"
    except Exception as e:
        logger.error(f"Whisper transcription failed: {str(e)}")
    
    logger.error("Both YouTube and Whisper failed")
    return None, "Failed to transcribe audio"
