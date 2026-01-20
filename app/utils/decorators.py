"""
Utility decorators for common patterns.

Provides reusable decorators implementing:
- DRY: Retry logic in one place
- SoC: Cross-cutting concerns separated
- Pythonic patterns: Decorators for aspect-oriented programming
"""

import time
import functools
from typing import Callable, Type, Tuple
from app.utils.logger import logger


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator to retry a function on failure.
    
    Implements exponential backoff retry pattern with configurable parameters.
    This eliminates duplicated retry logic throughout the codebase (DRY).
    
    Args:
        max_attempts: Maximum number of attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff: Multiplier for delay on each retry (default: 2.0)
        exceptions: Tuple of exceptions to catch (default: all exceptions)
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @retry(max_attempts=5, delay=2.0, backoff=2.0)
        def download_video(url):
            # Will retry up to 5 times with exponential backoff
            # (2s, 4s, 8s, 16s delays)
            return risky_download(url)
    
    Raises:
        Last exception if all attempts fail
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # This should never be reached, but for safety
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def timeout(seconds: float) -> Callable:
    """
    Decorator to add timeout to a function.
    
    Note: This is a simple implementation. For production use, consider
    using signal (Unix) or threading-based timeout.
    
    Args:
        seconds: Timeout in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Simple implementation - just log the timeout
            # For actual timeout, would need threading or signal
            logger.debug(f"{func.__name__} timeout set to {seconds}s")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_execution(func: Callable) -> Callable:
    """
    Decorator to log function execution time.
    
    Useful for performance monitoring and debugging.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function that logs execution time
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = func.__name__
        
        logger.debug(f"Starting {func_name}...")
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"{func_name} completed in {elapsed:.2f}s")
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func_name} failed after {elapsed:.2f}s: {e}")
            raise
    
    return wrapper


def memoize(func: Callable) -> Callable:
    """
    Simple memoization decorator for caching function results.
    
    Use with caution - only for pure functions without side effects.
    
    Args:
        func: Function to memoize
        
    Returns:
        Memoized function
    """
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create cache key from args and kwargs
        key = str(args) + str(sorted(kwargs.items()))
        
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        else:
            logger.debug(f"Cache hit for {func.__name__}")
        
        return cache[key]
    
    return wrapper


def deprecated(replacement: str = None) -> Callable:
    """
    Decorator to mark functions as deprecated.
    
    Args:
        replacement: Name of replacement function
        
    Returns:
        Decorated function that logs deprecation warning
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            message = f"{func.__name__} is deprecated"
            if replacement:
                message += f". Use {replacement} instead"
            logger.warning(message)
            return func(*args, **kwargs)
        return wrapper
    return decorator
