"""
API routes for the YouTube Summarizer application.
Handles transcript generation, summarization, and hybrid outputs.

Refactored to use:
- Custom exception hierarchy (Fail Fast, EAFP)
- Data models for validation (DRY, SRP)
- Middleware for error handling (SoC)
"""
import time
import os
import subprocess
from io import BytesIO
from datetime import datetime
from flask import Blueprint, request, send_file

from app.config import config
from app.utils.logger import logger
from app.utils.responses import success_response, error_response, validation_error_response
from app.exceptions import ValidationError, TranscriptError, SummarizationError
from app.validators import (
    validate_youtube_url,
    validate_transcript_file,
    validate_summary_type,
    validate_output_format
)
from app.services.youtube_service import (
    get_transcript,
    extract_video_id,
    get_video_title,
    get_diarized_transcript
)
from app.services.summarization_service import (
    summarize_with_perplexity,
    summarize_with_gemini
)
from app.services.pdf_service import create_pdf_summary, create_hybrid_pdf
from app.utils.parsers import parse_transcript_file
from app.constants import (
    ERROR_NO_URL,
    ERROR_NO_FILE,
    ERROR_NO_URL_OR_FILE,
    ERROR_TRANSCRIPT_FAILED,
    ERROR_SUMMARIZATION_FAILED,
    SUCCESS_TRANSCRIPT_READY,
    DEBUG_ENDPOINT_TIMEOUT,
    COOKIES_FILENAME
)

bp = Blueprint('api', __name__, url_prefix='/api')


# ============================================================================
# Health & Debug Endpoints
# ============================================================================

@bp.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint.
    
    Returns application status and configuration info.
    Uses HealthResponse model for consistent response format.
    """
    from app.models import HealthResponse
    from app.config import config
    from app.utils.responses import success_response
    
    logger.debug("Health check")
    
    response = HealthResponse(
        version='2.0.0',
        sections=['transcript', 'summarize'],
        perplexity_configured=config.use_perplexity,
        gemini_configured=bool(config.google_api_key),
        ai_provider=config.ai_provider
    )
    
    return success_response(response.to_dict())


@bp.route('/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to check yt-dlp version and environment."""
    try:
        import yt_dlp
        yt_dlp_version = yt_dlp.version.__version__

        # Try to fetch formats for a sample video
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        formats_info = "N/A"

        try:
            cmd = ["yt-dlp", "-F", video_url]

            # Use cookies if available
            cookies_path = os.path.join(os.getcwd(), COOKIES_FILENAME)
            if os.path.exists(cookies_path):
                cmd.extend(["--cookiefile", cookies_path])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=DEBUG_ENDPOINT_TIMEOUT
            )
            formats_info = result.stdout[:1000]
        except Exception as e:
            formats_info = f"Error fetching formats: {str(e)}"

        return success_response({
            'yt_dlp_version': yt_dlp_version,
            'ffmpeg_installed': subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True
            ).returncode == 0,
            'cookies_detected': os.path.exists(
                os.path.join(os.getcwd(), COOKIES_FILENAME)
            ),
            'env': {
                k: v for k, v in os.environ.items()
                if "KEY" not in k.upper() and "SECRET" not in k.upper()
            },
            'sample_formats': formats_info
        })
    except Exception as e:
        return error_response(str(e), status_code=500)


# ============================================================================
# Transcript Endpoints
# ============================================================================

@bp.route('/transcript', methods=['POST'])
def get_transcript_only():
    """
    Generate transcript only (without summarization).
    
    Refactored to use:
    - TranscriptRequest model for validation
    - Custom exceptions (Fail Fast, EAFP)
    - Error middleware handles all exceptions
    """
    from app.models import TranscriptRequest, TranscriptResponse
    
    # EAFP: Try to process, handle errors if they occur
    try:
        data = request.get_json()
        if not data:
            raise ValidationError('body', 'Invalid JSON')
        
        # Create and validate request model (Fail Fast validation in __post_init__)
        request_data = TranscriptRequest(**data)
        
        logger.info(
            f"Processing transcript request: {request_data.url} "
            f"(Diarization: {request_data.diarization})"
        )
        
        # Generate transcript
        if request_data.diarization:
            transcript, source = get_diarized_transcript(request_data.url)
        else:
            transcript, source = get_transcript(request_data.url)
        
        if not transcript:
            raise TranscriptError(source or "Transcript generation failed", source)
        
        logger.info(f"[OK] {SUCCESS_TRANSCRIPT_READY} - source: {source}")
        
        # Use response model
        response = TranscriptResponse(
            transcript=transcript,
            source=source,
            filename=f'transcript_{request_data.video_id}_{source}.txt',
            video_id=request_data.video_id
        )
        
        return success_response(response.to_dict(), message=SUCCESS_TRANSCRIPT_READY)
    
    except (ValidationError, TranscriptError):
        # Re-raise for error middleware to handle
        raise
    except Exception as e:
        logger.error(f"Transcript endpoint error: {str(e)}")
        raise TranscriptError(str(e))


@bp.route('/upload-transcript', methods=['POST'])
def validate_transcript():
    """Validate uploaded transcript file."""
    try:
        logger.info(">>> ENDPOINT: /api/upload-transcript <<<")

        if 'file' not in request.files:
            return error_response(ERROR_NO_FILE)

        file = request.files['file']

        # Validate file
        is_valid, error_msg = validate_transcript_file(file)
        if not is_valid:
            return validation_error_response('file', error_msg)

        logger.info(f"[PROCESS] Validating file: {file.filename}")

        # Read and validate content
        content = file.read().decode('utf-8')
        file_size = len(content)
        word_count = len(content.split())

        logger.info("[OK] File validated")
        logger.info(f"[STATS] Size: {file_size} characters | Words: {word_count}")

        preview = content[:200] + '...' if len(content) > 200 else content

        return success_response({
            'filename': file.filename,
            'size': file_size,
            'words': word_count,
            'preview': preview
        })

    except Exception as e:
        logger.error(f"Upload validation error: {str(e)}")
        return error_response(str(e), status_code=500)


# ============================================================================
# Helper Functions for Summarization
# ============================================================================

def _get_transcript_from_request():
    """Extract transcript from request (either from URL or file upload)."""
    # Handle JSON requests
    if request.is_json:
        data = request.json
        video_url = data.get('url', '').strip()
        summary_type = data.get('type', 'normal')
        output_format = data.get('format', 'pdf')
        transcript_file = None

    # Handle form data (file upload)
    else:
        video_url = request.form.get('url', '').strip()
        summary_type = request.form.get('type', 'normal')
        output_format = request.form.get('format', 'pdf')
        transcript_file = request.files.get('transcript_file')

    # Validate and normalize
    summary_type = validate_summary_type(summary_type)
    output_format = validate_output_format(output_format)

    # Option 1: File upload
    if transcript_file:
        logger.info(">>> ENDPOINT: /api/summarize (FILE UPLOAD MODE) <<<")

        is_valid, error_msg = validate_transcript_file(transcript_file)
        if not is_valid:
            return None, None, None, None, error_msg

        try:
            content = transcript_file.read().decode('utf-8')
            transcript = parse_transcript_file(content)
            source = "file_upload"
            video_id = 'manual_upload'
            title = transcript_file.filename.replace('.txt', '')

            logger.info(f"[OK] Transcript extracted ({len(transcript)} chars)")
            return transcript, source, video_id, title, None

        except Exception as e:
            return None, None, None, None, f'Could not read file: {e}'

    # Option 2: Video URL
    elif video_url:
        logger.info(">>> ENDPOINT: /api/summarize (VIDEO URL MODE) <<<")
        logger.info(f"Video: {video_url} | Type: {summary_type} | Format: {output_format}")

        is_valid, error_msg = validate_youtube_url(video_url)
        if not is_valid:
            return None, None, None, None, error_msg

        transcript, source = get_transcript(video_url)

        if not transcript:
            logger.error(f"Summarize: Transcript failed - {source}")
            return None, None, None, None, source or ERROR_TRANSCRIPT_FAILED

        video_id = extract_video_id(video_url)
        title = get_video_title(video_url) or f'Video {video_id}'

        logger.info(f"Transcript ready ({len(transcript)} chars)")
        return transcript, source, video_id, title, None

    # No transcript or URL provided
    else:
        return None, None, None, None, ERROR_NO_URL_OR_FILE


def _generate_summary(transcript: str, summary_type: str) -> tuple[str, str]:
    """Generate summary using configured AI service."""
    logger.info(f"[START] Summarization process ({summary_type} mode)")

    summary = None

    if Config.USE_PERPLEXITY:
        logger.info("Using Perplexity API...")
        summary = summarize_with_perplexity(transcript, summary_type)

        if not summary and Config.GOOGLE_API_KEY:
            logger.warning("Perplexity failed, trying Gemini...")
            summary = summarize_with_gemini(transcript, summary_type)
    else:
        logger.info("Using Gemini API...")
        summary = summarize_with_gemini(transcript, summary_type)

    if not summary:
        logger.error("All summarization APIs failed")
        return None, ERROR_SUMMARIZATION_FAILED

    logger.info(f"[OK] Summary generated ({len(summary)} characters)")
    return summary, None


# ============================================================================
# Summarization Endpoints
# ============================================================================

@bp.route('/summarize', methods=['POST'])
def summarize_transcript():
    """Summarize transcript from video URL or uploaded file."""
    try:
        start_time = time.time()

        # Get summary type and output format
        if request.is_json:
            summary_type = validate_summary_type(request.json.get('type'))
            output_format = validate_output_format(request.json.get('format'))
            video_url = request.json.get('url', '').strip()
        else:
            summary_type = validate_summary_type(request.form.get('type'))
            output_format = validate_output_format(request.form.get('format'))
            video_url = request.form.get('url', '').strip()

        # Get transcript
        transcript, source, video_id, title, error = _get_transcript_from_request()
        if error:
            return error_response(error)

        # Generate summary
        summary, error = _generate_summary(transcript, summary_type)
        if error:
            return error_response(error, status_code=500)

        # Generate output based on format
        if output_format == 'pdf':
            logger.info("[EXPORT] Creating PDF...")
            pdf_buffer = create_pdf_summary(
                title, summary, video_url or 'Manual Upload',
                source, summary_type
            )

            elapsed_time = time.time() - start_time
            logger.info(
                f"[COMPLETE] Summary PDF ready for download "
                f"({elapsed_time:.1f}s total)"
            )

            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'summary_{video_id}_{summary_type}.pdf'
            )

        else:  # txt format
            logger.info("[EXPORT] Creating TXT...")
            content = f"""SUMMARY - {summary_type.upper()}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source: {source.upper()}
{'Video: ' + video_url if video_url else 'File: ' + title}

{'=' * 80}

{summary}

{'=' * 80}

Generated by YouTube Summarizer
"""
            buffer = BytesIO()
            buffer.write(content.encode('utf-8'))
            buffer.seek(0)

            elapsed_time = time.time() - start_time
            logger.info(
                f"[COMPLETE] Summary TXT ready for download "
                f"({elapsed_time:.1f}s total)"
            )

            return send_file(
                buffer,
                mimetype='text/plain',
                as_attachment=True,
                download_name=f'summary_{video_id}_{summary_type}.txt'
            )

    except Exception as e:
        logger.error(f"Summarize endpoint error: {str(e)}")
        import traceback
        logger.error(f"[TRACEBACK]\n{traceback.format_exc()}")
        return error_response(str(e), status_code=500)


@bp.route('/hybrid', methods=['POST'])
def hybrid_output():
    """Generate hybrid PDF with transcript and summary."""
    try:
        data = request.json
        if not data:
            return validation_error_response('body', 'Invalid JSON')

        video_url = data.get('url', '').strip()
        summary_type = validate_summary_type(data.get('type'))

        if not video_url:
            return error_response(ERROR_NO_URL)

        is_valid, error_msg = validate_youtube_url(video_url)
        if not is_valid:
            return validation_error_response('url', error_msg)

        logger.info(">>> ENDPOINT: /api/hybrid <<<")
        logger.info(f"Video: {video_url} | Type: {summary_type}")

        # Get transcript
        transcript, source = get_transcript(video_url)
        if not transcript:
            logger.error(f"Hybrid: Transcript failed - {source}")
            return error_response(source or ERROR_TRANSCRIPT_FAILED)

        logger.info(f"Transcript ready ({len(transcript)} chars)")

        # Generate summary
        summary, error = _generate_summary(transcript, summary_type)
        if error:
            return error_response(error, status_code=500)

        # Create hybrid PDF
        title = data.get('title', f'Video {extract_video_id(video_url)}')
        pdf_buffer = create_hybrid_pdf(
            title, summary, transcript, video_url, source, summary_type
        )

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'hybrid_{extract_video_id(video_url)}.pdf'
        )

    except Exception as e:
        logger.error(f"Hybrid endpoint error: {str(e)}")
        return error_response(str(e), status_code=500)
