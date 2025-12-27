import time
from google import genai
from app.config import Config
from app.utils.logger import logger

def transcribe_with_gemini(audio_path):
    """
    Uploads audio to Gemini and requests transcription with speaker identification.
    Returns: (transcript_text, "gemini")
    """
    try:
        if not Config.GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY not found")
            return None, "Missing API Key"

        client = genai.Client(api_key=Config.GOOGLE_API_KEY)

        logger.info(f"Uploading audio to Gemini: {audio_path}")

        # 1. Upload file
        audio_file = client.files.upload(file=audio_path)

        # 2. Wait for processing
        while audio_file.state.name == "PROCESSING":
            logger.info("Waiting for audio processing...")
            time.sleep(2)
            audio_file = client.files.get(name=audio_file.name)

        if audio_file.state.name == "FAILED":
            logger.error("Gemini audio processing failed")
            return None, "Gemini processing failed"

        logger.info("Audio ready. Generating transcript...")

        # 3. Generate Content
        # Using gemini-1.5-flash as it is the current stable flash model
        model_id = "gemini-1.5-flash"
        
        prompt = """
        Transcribe this audio in Polish.
        Identify different speakers (e.g., Speaker 1, Speaker 2).
        Format exactly like this:
        [MM:SS] Speaker 1: Text...
        [MM:SS] Speaker 2: Text...

        Ensure timestamps correspond to the start of the sentence.
        """

        response = client.models.generate_content(
            model=model_id,
            contents=[prompt, audio_file]
        )

        transcript = response.text
        logger.info(f"[OK] Gemini transcription complete ({len(transcript)} chars)")

        # Cleanup (optional, but good practice)
        # Note: The new SDK might handle cleanup differently or not expose a direct delete checked here.
        # We can try to delete if supported, otherwise skip.
        try:
             client.files.delete(name=audio_file.name)
        except Exception:
            pass

        return transcript, "gemini"

    except Exception as e:
        logger.error(f"Gemini Audio Error: {str(e)}")
        return None, str(e)
