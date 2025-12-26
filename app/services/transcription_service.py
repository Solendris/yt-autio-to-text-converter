import os
from faster_whisper import WhisperModel
from app.utils.logger import logger
from app.utils.formatting import format_seconds

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
        logger.info("Transcribing with Whisper...")

        model = init_whisper()
        segments, info = model.transcribe(audio_path, language="pl", beam_size=5)

        formatted_lines = []
        for segment in segments:
            # Whisper segments usually have 'start', 'end', 'text'
            text = segment.text.strip()
            if text:
                timestamp = format_seconds(segment.start)
                formatted_lines.append(f"{timestamp} {text}")

        transcript = '\n'.join(formatted_lines)

        logger.info(f"[OK] Transcription complete ({len(transcript)} characters)")

        try:
            os.remove(audio_path)
        except OSError:
            pass

        return transcript

    except Exception as e:
        logger.error(f"Whisper error: {str(e)}")
        return None
