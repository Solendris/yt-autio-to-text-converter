"""
Authentication middleware for API key validation.

This module implements API key authentication to prevent unauthorized access.
Addresses: Critical Vulnerability #1 - Lack of Authentication
"""

import os
from functools import wraps
from flask import request
from app.utils.responses import error_response
from app.utils.logger import logger


def require_api_key(f):
    """
    Decorator to require valid API key for endpoint access.
    
    Checks for X-API-Key header and validates against configured API_KEY.
    Returns 401 Unauthorized if key is missing or invalid.
    
    Usage:
        @bp.route('/transcript', methods=['POST'])
        @require_api_key
        def get_transcript():
            # Your code here
    
    Args:
        f: Function to wrap
        
    Returns:
        Wrapped function with API key validation
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        
        # Get expected API key from environment
        expected_key = os.getenv('API_KEY', '').strip()
        
        # Check if API key is configured
        if not expected_key:
            logger.error("API_KEY not configured in environment")
            return error_response(
                'Server configuration error',
                status_code=500
            )
        
        # Validate API key
        if not api_key:
            logger.warning(f"Missing API key from {request.remote_addr}")
            return error_response(
                'Missing API key. Please provide X-API-Key header.',
                status_code=401
            )
        
        if api_key != expected_key:
            logger.warning(f"Invalid API key attempt from {request.remote_addr}")
            return error_response(
                'Invalid API key',
                status_code=401
            )
        
        # API key is valid, proceed with request
        logger.debug(f"API key validated for {request.remote_addr}")
        return f(*args, **kwargs)
    
    return decorated_function
