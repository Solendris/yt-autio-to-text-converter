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
    
    For public portfolio apps, this allows two authentication methods:
    1. API Key (X-API-Key header) - for direct API access
    2. Whitelisted Origin - for public frontend (relies on CORS + rate limiting)
    
    Whitelisted origins can access without API key, protected by:
    - CORS (only specific domains can make browser requests)
    - Rate limiting (prevents abuse)
    
    This balances security with usability for public portfolio applications.
    
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
        # Whitelisted origins (public frontend)
        # These can access without API key, protected by CORS + rate limiting
        WHITELISTED_ORIGINS = [
            'https://solendris.github.io',
            'http://localhost:5173',
            'http://127.0.0.1:5173'
        ]
        
        # Check if request is from whitelisted origin
        # Note: Browsers send 'Origin' for POST/PUT/DELETE and CORS preflight,
        # but may only send 'Referer' for simple GET requests
        origin = request.headers.get('Origin', '')
        referer = request.headers.get('Referer', '')
        
        # Check Origin first
        if origin in WHITELISTED_ORIGINS:
            logger.info(f"Request from whitelisted origin (Origin header): {origin}")
            return f(*args, **kwargs)
        
        # Fallback: check if Referer starts with whitelisted origin
        for whitelisted in WHITELISTED_ORIGINS:
            if referer.startswith(whitelisted):
                logger.info(f"Request from whitelisted origin (Referer header): {referer}")
                return f(*args, **kwargs)
        
        # For non-whitelisted origins, require API key
        api_key = request.headers.get('X-API-Key')
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
            logger.warning(f"Missing API key from {request.remote_addr} (origin: {origin})")
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
