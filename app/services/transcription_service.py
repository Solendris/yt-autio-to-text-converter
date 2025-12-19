import os
from faster_whisper import WhisperModel
from app.utils.logger import logger

whisper_model = None

def init_whisper():
    global whisper_model
    if whisper_model is None:
        logger.info("Initializing Whisper model...")
        whisper_model = WhisperModel("base", device="cpu", compute_type="float32")
        logger.info("[OK] Whisper model loaded")
    return whisper_model

def transcribe_with_whisper(audio_path):
    try:
        logger.info(f"Transcribing with Whisper...")
        
        model = init_whisper()
        segments, info = model.transcribe(audio_path, language="pl", beam_size=5)
        
        transcript = ' '.join([segment.text for segment in segments])
        
        logger.info(f"[OK] Transcription complete ({len(transcript)} characters)")
        
        try:
            os.remove(audio_path)
        except:
            pass
        
        return transcript
    
    except Exception as e:
        logger.error(f"Whisper error: {str(e)}")
        return None
