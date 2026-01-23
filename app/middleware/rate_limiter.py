"""
Simple in-memory rate limiter middleware.

This module implements rate limiting to prevent API abuse.
Addresses: Critical Vulnerability #4 - Lack of Rate Limiting

Note: This is a simple in-memory implementation suitable for single-instance deployments.
For production clusters, consider using Redis-backed solution (Flask-Limiter).
"""

import time
from functools import wraps
from collections import defaultdict, deque
from flask import request
from app.utils.responses import error_response
from app.utils.logger import logger


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window algorithm.
    
    Tracks requests per IP address within a time window.
    """
    
    def __init__(self):
        """Initialize rate limiter with empty request tracking."""
        # Store timestamps of requests per IP
        # Format: {ip_address: deque([timestamp1, timestamp2, ...])}
        self.requests = defaultdict(deque)
    
    def is_allowed(self, identifier: str, limit: int, window: int) -> bool:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            identifier: Unique identifier (e.g., IP address)
            limit: Maximum number of requests allowed
            window: Time window in seconds
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        now = time.time()
        
        # Get request history for this identifier
        request_times = self.requests[identifier]
        
        # Remove timestamps outside the window
        cutoff = now - window
        while request_times and request_times[0] < cutoff:
            request_times.popleft()
        
        # Check if limit is exceeded
        if len(request_times) >= limit:
            return False
        
        # Add current request timestamp
        request_times.append(now)
        return True
    
    def cleanup(self):
        """
        Remove old entries to prevent memory buildup.
        Should be called periodically (e.g., every hour).
        """
        now = time.time()
        cutoff = now - 3600  # Remove entries older than 1 hour
        
        # Remove old timestamps from all identifiers
        for identifier in list(self.requests.keys()):
            request_times = self.requests[identifier]
            while request_times and request_times[0] < cutoff:
                request_times.popleft()
            
            # Remove identifier if no recent requests
            if not request_times:
                del self.requests[identifier]


# Global rate limiter instance
_limiter = RateLimiter()


def rate_limit(max_requests: int = 50, window_seconds: int = 3600):
    """
    Decorator to apply rate limiting to an endpoint.
    
    Default: 50 requests per hour (3600 seconds)
    
    Usage:
        @bp.route('/transcript', methods=['POST'])
        @rate_limit(max_requests=50, window_seconds=3600)
        def get_transcript():
            # Your code here
    
    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use IP address as identifier
            identifier = request.remote_addr
            
            if not _limiter.is_allowed(identifier, max_requests, window_seconds):
                logger.warning(
                    f"Rate limit exceeded for {identifier}: "
                    f"{max_requests} requests per {window_seconds}s"
                )
                return error_response(
                    f'Rate limit exceeded. Maximum {max_requests} requests per hour.',
                    status_code=429
                )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def get_rate_limiter() -> RateLimiter:
    """
    Get the global rate limiter instance.
    
    Returns:
        Global RateLimiter instance
    """
    return _limiter
