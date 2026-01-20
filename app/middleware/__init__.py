"""
Middleware for request validation and response processing.

This module provides decorators for common request validation patterns,
implementing:
- DRY: Reusable validation logic
- SoC: Separates validation from business logic
- EAFP: Pythonic error handling with try/except
"""

from functools import wraps
from typing import Type, TypeVar, Callable
from flask import request
from app.exceptions import ValidationError
from app.utils.logger import logger

T = TypeVar('T')


def validate_json(model_class: Type[T]) -> Callable:
    """
    Decorator to validate request JSON against a data model.
    
    This implements:
    - DRY: Validation logic in one place
    - SRP: Route handlers don't need to validate
    - Fail Fast: Invalid requests are rejected immediately
    - EAFP: Use try/except instead of checks
    
    Args:
        model_class: Dataclass model to validate against
        
    Returns:
        Decorated function that receives validated model instance
        
    Example:
        @app.route('/transcript', methods=['POST'])
        @validate_json(TranscriptRequest)
        def get_transcript(request_data: TranscriptRequest):
            # request_data is already validated!
            return controller.handle(request_data)
    
    Raises:
        ValidationError: If JSON is invalid or validation fails
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # EAFP: Try to parse JSON, handle errors if it fails
                data = request.get_json()
                if data is None:
                    raise ValidationError('body', 'Invalid JSON or empty request body')
                
                # Instantiate model - validation happens in __post_init__
                validated_data = model_class(**data)
                
                logger.debug(f"Request validated: {model_class.__name__}")
                
                # Pass validated model to route handler
                return f(validated_data, *args, **kwargs)
                
            except TypeError as e:
                # Model instantiation failed (missing/extra fields)
                raise ValidationError('body', f"Invalid request format: {str(e)}")
            except ValidationError:
                # Re-raise validation errors from model
                raise
            except Exception as e:
                # Unexpected error during validation
                logger.error(f"Validation error: {str(e)}")
                raise ValidationError('request', f"Request validation failed: {str(e)}")
        
        return wrapper
    return decorator


def validate_form_data(model_class: Type[T]) -> Callable:
    """
    Decorator to validate form data (for file uploads).
    
    Similar to validate_json but handles multipart/form-data requests.
    
    Args:
        model_class: Dataclass model to validate against
        
    Returns:
        Decorated function that receives validated model instance
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Extract form data
                data = {}
                
                # Get regular form fields
                for key in request.form:
                    data[key] = request.form[key]
                
                # Handle file uploads
                if 'transcript_file' in request.files:
                    file = request.files['transcript_file']
                    if file and file.filename:
                        # Validate file
                        from app.validators import validate_transcript_file
                        is_valid, error_msg = validate_transcript_file(file)
                        if not is_valid:
                            raise ValidationError('transcript_file', error_msg)
                        
                        # Read file content
                        content = file.read().decode('utf-8')
                        data['transcript_text'] = content
                        data['filename'] = file.filename
                
                # Validate with model
                validated_data = model_class(**data)
                
                logger.debug(f"Form data validated: {model_class.__name__}")
                
                return f(validated_data, *args, **kwargs)
                
            except TypeError as e:
                raise ValidationError('form', f"Invalid form data: {str(e)}")
            except ValidationError:
                raise
            except UnicodeDecodeError:
                raise ValidationError('transcript_file', 'File must be UTF-8 encoded text')
            except Exception as e:
                logger.error(f"Form validation error: {str(e)}")
                raise ValidationError('form', f"Form validation failed: {str(e)}")
        
        return wrapper
    return decorator


def require_fields(*field_names: str) -> Callable:
    """
    Decorator to ensure required fields are present in request.
    
    Use for simple validations before more complex processing.
    
    Args:
        *field_names: Names of required fields
        
    Returns:
        Decorated function
        
    Example:
        @app.route('/process', methods=['POST'])
        @require_fields('url', 'type')
        def process():
            # url and type are guaranteed to exist
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json() or {}
            
            for field in field_names:
                if field not in data or not data[field]:
                    raise ValidationError(field, f"Field '{field}' is required")
            
            return f(*args, **kwargs)
        
        return wrapper
    return decorator


def log_request(f: Callable) -> Callable:
    """
    Decorator to log incoming requests.
    
    Useful for debugging and monitoring.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        logger.info(f">>> ENDPOINT: {request.endpoint} <<<")
        logger.debug(f"Method: {request.method}, Path: {request.path}")
        
        return f(*args, **kwargs)
    
    return wrapper
