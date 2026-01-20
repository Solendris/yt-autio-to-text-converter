"""
Error handling middleware.

Centralized error handling for the application, implementing:
- DRY: Single place for error handling logic
- SoC: Separates error handling from business logic
- Fail Fast: Errors are caught and handled appropriately
- Consistent API responses
"""

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from app.exceptions import (
    AppException,
    ValidationError,
    ConfigurationError,
    TranscriptError,
    SummarizationError,
    FileProcessingError,
    ExternalServiceError,
    ResourceNotFoundError
)
from app.utils.logger import logger
from app.utils.responses import error_response


def register_error_handlers(app: Flask):
    """
    Register global error handlers for the Flask application.
    
    This centralizes error handling, ensuring:
    - Consistent error response format
    - Appropriate HTTP status codes
    - Proper logging
    - No sensitive information leakage
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(e: ValidationError):
        """Handle input validation errors (400 Bad Request)."""
        logger.warning(f"Validation error: {e.message}")
        return error_response(
            error='Validation error',
            status_code=e.status_code,
            details=e.details
        )
    
    @app.errorhandler(ConfigurationError)
    def handle_configuration_error(e: ConfigurationError):
        """
        Handle configuration errors (500 Internal Server Error).
        
        These should only occur during startup due to Fail Fast,
        but this handler provides a safety net.
        """
        logger.error(f"Configuration error: {e.message}")
        return error_response(
            error='Server configuration error',
            status_code=500
        )
    
    @app.errorhandler(TranscriptError)
    def handle_transcript_error(e: TranscriptError):
        """Handle transcript generation errors."""
        logger.error(f"Transcript error: {e.message}")
        return error_response(
            error=e.message,
            status_code=e.status_code,
            details=e.details
        )
    
    @app.errorhandler(SummarizationError)
    def handle_summarization_error(e: SummarizationError):
        """Handle summarization errors."""
        logger.error(f"Summarization error: {e.message}")
        return error_response(
            error=e.message,
            status_code=e.status_code,
            details=e.details
        )
    
    @app.errorhandler(FileProcessingError)
    def handle_file_error(e: FileProcessingError):
        """Handle file processing errors."""
        logger.warning(f"File processing error: {e.message}")
        return error_response(
            error=e.message,
            status_code=e.status_code,
            details=e.details
        )
    
    @app.errorhandler(ExternalServiceError)
    def handle_external_service_error(e: ExternalServiceError):
        """Handle external service errors."""
        logger.error(f"External service error: {e.message}")
        return error_response(
            error=f"{e.service_name} service is currently unavailable",
            status_code=e.status_code,
            details={'service': e.service_name}
        )
    
    @app.errorhandler(ResourceNotFoundError)
    def handle_not_found_error(e: ResourceNotFoundError):
        """Handle resource not found errors."""
        logger.warning(f"Resource not found: {e.message}")
        return error_response(
            error=e.message,
            status_code=e.status_code,
            details=e.details
        )
    
    @app.errorhandler(AppException)
    def handle_app_exception(e: AppException):
        """Handle all other application exceptions."""
        logger.error(f"Application error: {e.message}")
        return error_response(
            error=e.message,
            status_code=e.status_code,
            details=e.details
        )
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        """Handle Werkzeug HTTP exceptions (404, 405, etc.)."""
        logger.warning(f"HTTP error {e.code}: {e.description}")
        return error_response(
            error=e.description,
            status_code=e.code
        )
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(e: Exception):
        """
        Handle unexpected errors (500 Internal Server Error).
        
        This is a catch-all for errors that slip through.
        Always log the full traceback for debugging.
        """
        import traceback
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        
        # Don't expose internal error details to client
        return error_response(
            error='An unexpected error occurred',
            status_code=500
        )


def register_request_logging(app: Flask):
    """
    Register request/response logging middleware.
    
    Logs all requests and responses for debugging and monitoring.
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def log_request_info():
        """Log incoming request details."""
        from flask import request
        logger.debug(
            f"Request: {request.method} {request.path} "
            f"from {request.remote_addr}"
        )
    
    @app.after_request
    def log_response_info(response):
        """Log outgoing response details."""
        logger.debug(f"Response: {response.status_code}")
        return response


def init_middleware(app: Flask):
    """
    Initialize all middleware for the application.
    
    This should be called during application factory setup.
    
    Args:
        app: Flask application instance
    """
    logger.info("Registering error handlers...")
    register_error_handlers(app)
    
    if app.config.get('DEBUG'):
        logger.info("Registering request logging (debug mode)...")
        register_request_logging(app)
    
    logger.info("Middleware initialization complete")
