import time
from typing import Tuple, Optional
from google import genai
from app.config import config
from app.utils.logger import logger
from app.constants import GEMINI_MODEL


def transcribe_with_gemini(
    audio_path: str, 
    title: Optional[str] = None, 
    duration: Optional[str] = None
) -> Tuple[Optional[str], str]:
    """
    Uploads audio to Gemini and requests transcription with speaker identification.

    Args:
        audio_path: Path to the local audio file.
        title: Optional video title for context.
        duration: Optional video duration for context.

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

        # 2. Encapsulate in try-finally to ensure cleanup (Fix for Leaking Resources)
        try:
            # 2a. Wait for processing
            while audio_file.state.name == "PROCESSING":
                logger.info("Waiting for audio processing...")
                time.sleep(2)
                audio_file = client.files.get(name=audio_file.name)

            if audio_file.state.name == "FAILED":
                logger.error("Gemini audio processing failed")
                return None, "Gemini processing failed"

            logger.info("Audio ready. Generating transcript...")

            # 3. Generate Content
            # Provide metadata for "grounding" to prevent timestamp hallucinations
            context_str = ""
            if title or duration:
                context_str = "\nKontekst nagrania:\n"
                if title: context_str += f"- Tytuł: {title}\n"
                if duration: context_str += f"- Czas trwania: {duration}\n"

            prompt = f"""
            Transkrybuj to nagranie audio w języku polskim.{context_str}
            
            WAŻNE INSTRUKCJE:
            1. Rozpoznaj różnych mówców (np. Speaker 1, Speaker 2).
            2. Formatuj KAŻDĄ linię dokładnie tak:
               [HH:MM:SS] Speaker X: Treść...
            3. Używaj PEŁNEGO formatu czasu [godziny:minuty:sekundy], nawet jeśli film jest krótki.
            4. Znaczniki czasu MUSZĄ odpowiadać rzeczywistemu momentowi w nagraniu.
            5. Nie wymyślaj czasu wykraczającego poza czas trwania nagrania. Jeśli nagranie ma {duration or 'określony czas'}, ostatni znacznik musi być przed tą wartością.
            6. Pisz poprawną polszczyzną, zachowując naturalny sposób mówienia.
            """

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt, audio_file]
            )

            # 4. Handle response safely
            # Check if response has text (it might be blocked by safety filters or empty)
            transcript = getattr(response, 'text', None)
            
            if not transcript:
                finish_reason = "UNKNOWN"
                if hasattr(response, 'candidates') and response.candidates:
                    finish_reason = response.candidates[0].finish_reason.name
                
                error_msg = f"Gemini returned no text (Reason: {finish_reason})"
                logger.error(error_msg)
                return None, error_msg

            logger.info(f"[OK] Gemini transcription complete ({len(transcript)} chars)")
            return transcript, "gemini"

        finally:
            # 5. Cleanup - Always run this (Fix for Remote File Leak)
            logger.info(f"Cleaning up remote file: {audio_file.name}")
            try:
                client.files.delete(name=audio_file.name)
                logger.info("[OK] Remote file deleted")
            except Exception as e:
                logger.warning(f"Failed to delete remote Gemini file: {str(e)}")

    except Exception as e:
        logger.error(f"Gemini Audio Error: {str(e)}")
        return None, str(e)
