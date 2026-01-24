"""
API routes for the YouTube Summarizer application.
Handles transcript generation, summarization, and hybrid outputs using Controllers.
KISS: Routes serve as a thin layer to dispatch requests to Controllers.
"""
from io import BytesIO
import time
from datetime import datetime
from flask import Blueprint, request, send_file

from app.utils.logger import logger
from app.utils.responses import success_response, error_response, validation_error_response
from app.exceptions import ValidationError, TranscriptError, SummarizationError
from app.middleware.auth import require_api_key
from app.middleware.rate_limiter import rate_limit
from app.models import TranscriptRequest
from app.controllers import HealthController, TranscriptController, SummaryController
from app.validators import (
    validate_youtube_url,
    validate_transcript_file,
    validate_summary_type,
    validate_output_format
)
from app.constants import (
    ERROR_NO_URL,
    ERROR_NO_FILE,
    ERROR_NO_URL_OR_FILE,
    SUCCESS_TRANSCRIPT_READY,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW
)
from app.utils.parsers import parse_transcript_file

bp = Blueprint('api', __name__, url_prefix='/api')

# ============================================================================
# Health
# ============================================================================

@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    controller = HealthController()
    return success_response(controller.get_health_status())


# ============================================================================
# Transcript
# ============================================================================

@bp.route('/transcript', methods=['POST'])
@require_api_key
@rate_limit(max_requests=RATE_LIMIT_REQUESTS, window_seconds=RATE_LIMIT_WINDOW)
def get_transcript_only():
    """Generate transcript only."""
    try:
        data = request.get_json()
        if not data:
            raise ValidationError('body', 'Invalid JSON')
        
        request_data = TranscriptRequest(**data)
        
        controller = TranscriptController()
        response = controller.generate_transcript(request_data)
        
        return success_response(response.to_dict(), message=SUCCESS_TRANSCRIPT_READY)
    
    except (ValidationError, TranscriptError):
        raise
    except Exception as e:
        logger.error(f"Transcript endpoint error: {e}")
        raise TranscriptError(str(e))


@bp.route('/upload-transcript', methods=['POST'])
def validate_transcript():
    """Validate uploaded transcript file."""
    try:
        if 'file' not in request.files:
            return error_response(ERROR_NO_FILE)

        file = request.files['file']
        is_valid, error_msg = validate_transcript_file(file)
        if not is_valid:
            return validation_error_response('file', error_msg)

        content = file.read().decode('utf-8')
        controller = TranscriptController()
        result = controller.validate_transcript_file(content, file.filename)
        
        return success_response(result)

    except Exception as e:
        logger.error(f"Upload validation error: {e}")
        return error_response(str(e), status_code=500)


# ============================================================================
# Summarize
# ============================================================================

@bp.route('/summarize', methods=['POST'])
@require_api_key
@rate_limit(max_requests=RATE_LIMIT_REQUESTS, window_seconds=RATE_LIMIT_WINDOW)
def summarize_transcript():
    """Summarize transcript from video URL or uploaded file."""
    try:
        start_time = time.time()
        
        # 1. Parse Input
        if request.is_json:
            data = request.json
            summary_type = validate_summary_type(data.get('type'))
            output_format = validate_output_format(data.get('format'))
            video_url = data.get('url', '').strip()
            transcript_file = None
        else:
            summary_type = validate_summary_type(request.form.get('type'))
            output_format = validate_output_format(request.form.get('format'))
            video_url = request.form.get('url', '').strip()
            transcript_file = request.files.get('transcript_file')

        controller = SummaryController()
        
        # 2. Get Transcript
        transcript = None
        source = 'unknown'
        title = 'Summary'
        video_id = 'unknown'

        if transcript_file:
            # File Upload Mode
            is_valid, error_msg = validate_transcript_file(transcript_file)
            if not is_valid:
                return validation_error_response('file', error_msg)
            
            content = transcript_file.read().decode('utf-8')
            transcript = parse_transcript_file(content)
            source = "file_upload"
            video_id = 'manual_upload'
            title = transcript_file.filename.replace('.txt', '')
            
        elif video_url:
            # URL Mode
            is_valid, error_msg = validate_youtube_url(video_url)
            if not is_valid:
                return validation_error_response('url', error_msg)
                
            transcript, source, video_id, title = controller.get_transcript_for_url(video_url)
            
        else:
            return error_response(ERROR_NO_URL_OR_FILE)

        # 3. Generate Summary
        summary = controller.generate_summary(transcript, summary_type)

        # 4. Generate Output (PDF/TXT)
        elapsed_time = time.time() - start_time
        logger.info(f"[COMPLETE] Summary ready ({elapsed_time:.1f}s total)")

        if output_format == 'pdf':
            pdf_buffer = controller.create_pdf(
                title, summary, video_url or 'Manual Upload', source, summary_type
            )
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'summary_{video_id}_{summary_type}.pdf'
            )
        else:
            # TXT output
            content = f"""SUMMARY - {summary_type.upper()}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source: {source.upper()}
{'Video: ' + video_url if video_url else 'File: ' + title}

{'=' * 80}

{summary}

{'=' * 80}

Generated by YouTube Summarizer
"""
            buffer = BytesIO(content.encode('utf-8'))
            return send_file(
                buffer,
                mimetype='text/plain',
                as_attachment=True,
                download_name=f'summary_{video_id}_{summary_type}.txt'
            )

    except ValidationError as e:
        return validation_error_response(e.field, e.message)
    except (TranscriptError, SummarizationError) as e:
        return error_response(str(e))
    except Exception as e:
        logger.error(f"Summarize endpoint error: {e}")
        import traceback
        logger.error(f"[TRACEBACK]\n{traceback.format_exc()}")
        return error_response(str(e), status_code=500)


@bp.route('/hybrid', methods=['POST'])
@require_api_key
@rate_limit(max_requests=RATE_LIMIT_REQUESTS, window_seconds=RATE_LIMIT_WINDOW)
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

        controller = SummaryController()

        # Get Transcript
        transcript, source, video_id, title_fetched = controller.get_transcript_for_url(video_url)
        title = data.get('title', title_fetched)

        # Generate Summary
        summary = controller.generate_summary(transcript, summary_type)

        # Create PDF
        pdf_buffer = controller.create_hybrid_pdf(
            title, summary, transcript, video_url, source, summary_type
        )

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'hybrid_{video_id}.pdf'
        )

    except Exception as e:
        logger.error(f"Hybrid endpoint error: {e}")
        return error_response(str(e), status_code=500)
