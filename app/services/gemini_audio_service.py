import time
from typing import Tuple, Optional
from google import genai
from app.config import config
from app.utils.logger import logger
from app.constants import GEMINI_MODEL


def transcribe_with_gemini(audio_path: str) -> Tuple[Optional[str], str]:
    """
    Uploads audio to Gemini and requests transcription with speaker identification.

    Args:
        audio_path: Path to the local audio file.

    Returns:
        Tuple of (transcript_text, "gemini") or (None, error_message).
    """
    try:
        if not config.google_api_key:
            logger.error("GOOGLE_API_KEY not found")
            return None, "Missing API Key"

        client = genai.Client(api_key=config.google_api_key)

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
        prompt = """
        Transcribe this audio in Polish.
        Identify different speakers (e.g., Speaker 1, Speaker 2).
        Format exactly like this:
        [MM:SS] Speaker 1: Text...
        [MM:SS] Speaker 2: Text...

        Ensure timestamps correspond to the start of the sentence.
        """

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt, audio_file]
        )

        transcript = response.text
        logger.info(f"[OK] Gemini transcription complete ({len(transcript)} chars)")

        # Cleanup (optional, but good practice)
        try:
            client.files.delete(name=audio_file.name)
        except Exception as e:
            logger.warning(f"Failed to delete remote Gemini file: {str(e)}")

        return transcript, "gemini"

    except Exception as e:
        logger.error(f"Gemini Audio Error: {str(e)}")
        return None, str(e)
