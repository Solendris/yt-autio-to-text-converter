"""
API routes for the YouTube Transcript application.
Handles transcript generation using Controllers.
KISS: Routes serve as a thin layer to dispatch requests to Controllers.
"""
from flask import Blueprint, request

from app.utils.logger import logger
from app.utils.responses import success_response, error_response, validation_error_response
from app.exceptions import ValidationError, TranscriptError
from app.middleware.auth import require_api_key
from app.middleware.rate_limiter import rate_limit
from app.models import TranscriptRequest
from app.controllers import HealthController, TranscriptController
from app.validators import (
    validate_youtube_url,
    validate_transcript_file
)
from app.constants import (
    ERROR_NO_FILE,
    SUCCESS_TRANSCRIPT_READY,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW
)

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



