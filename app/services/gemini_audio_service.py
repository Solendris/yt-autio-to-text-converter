import os
import time
import google.generativeai as genai
from app.config import Config
from app.utils.logger import logger

def init_genai():
    if not Config.GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY not found")
        return False
    genai.configure(api_key=Config.GOOGLE_API_KEY)
    return True

def transcribe_with_gemini(audio_path):
    """
    Uploads audio to Gemini and requests transcription with speaker identification.
    Returns: (transcript_text, "gemini")
    """
    try:
        if not init_genai():
            return None, "Missing API Key"

        logger.info(f"Uploading audio to Gemini: {audio_path}")
        
        # 1. Upload file
        audio_file = genai.upload_file(audio_path)
        
        # 2. Wait for processing
        while audio_file.state.name == "PROCESSING":
            logger.info("Waiting for audio processing...")
            time.sleep(2)
            audio_file = genai.get_file(audio_file.name)

        if audio_file.state.name == "FAILED":
            logger.error("Gemini audio processing failed")
            return None, "Gemini processing failed"

        logger.info("Audio ready. Generating transcript...")

        # 3. Generate Content
        # Using gemini-flash-latest as 2.0 gave quota error (limit: 0)
        model = genai.GenerativeModel("gemini-flash-latest")
        
        prompt = """
        Transcribe this audio in Polish. 
        Identify different speakers (e.g., Speaker 1, Speaker 2).
        Format exactly like this:
        [MM:SS] Speaker 1: Text...
        [MM:SS] Speaker 2: Text...
        
        Ensure timestamps correspond to the start of the sentence.
        """

        response = model.generate_content([prompt, audio_file])
        
        transcript = response.text
        logger.info(f"[OK] Gemini transcription complete ({len(transcript)} chars)")

        # Cleanup (optional, but good practice)
        try:
            audio_file.delete()
        except:
            pass

        return transcript, "gemini"

    except Exception as e:
        logger.error(f"Gemini Audio Error: {str(e)}")
        return None, str(e)
