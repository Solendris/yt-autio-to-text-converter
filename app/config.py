"""
Application configuration with validation.

This module implements:
- Fail Fast: Configuration is validated on application startup
- Convention over Configuration: Sensible defaults provided
- Type safety: All config values are typed
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv
from app.exceptions import ConfigurationError

load_dotenv()


def _get_env_bool(key: str, default: bool = False) -> bool:
    """Parse boolean from environment variable."""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def _get_env_int(key: str, default: int) -> int:
    """
    Parse integer from environment variable with validation.
    
    Implements Fail Fast - invalid values cause immediate error.
    """
    try:
        return int(os.getenv(key, str(default)))
    except ValueError as e:
        raise ConfigurationError(
            f"Invalid integer value for {key}: {os.getenv(key)}"
        ) from e


@dataclass
class Config:
    """
    Application configuration with automatic validation.
    
    This class implements the Fail Fast principle by validating
    all configuration on instantiation. Invalid configuration
    will prevent the application from starting.
    
    Environment Variables:
        GOOGLE_API_KEY: API key for Google Gemini (required)
        API_TIMEOUT: Timeout for API requests (seconds)
        YOUTUBE_TIMEOUT: Timeout for YouTube operations (seconds)
        MAX_TEXT_LENGTH: Maximum text length for processing
        DEBUG: Enable debug mode
    """
    
    # API Keys
    google_api_key: str = field(default_factory=lambda: os.getenv('GOOGLE_API_KEY', '').strip())
    api_key: str = field(default_factory=lambda: os.getenv('API_KEY', '').strip())
    
    # Timeouts (seconds)
    api_timeout: int = field(default_factory=lambda: _get_env_int('API_TIMEOUT', 120))
    youtube_timeout: int = field(default_factory=lambda: _get_env_int('YOUTUBE_TIMEOUT', 60))
    operation_timeout: int = field(default_factory=lambda: _get_env_int('OPERATION_TIMEOUT', 300))
    
    # Processing Limits
    max_text_length: int = field(default_factory=lambda: _get_env_int('MAX_TEXT_LENGTH', 20000))
    max_video_duration: int = field(default_factory=lambda: _get_env_int('MAX_VIDEO_DURATION', 5400))
    
    # Feature Flags
    debug: bool = field(default_factory=lambda: _get_env_bool('DEBUG', False))
    
    def __post_init__(self):
        """
        Validate configuration on initialization.
        
        This implements Fail Fast - the application will not start
        with invalid configuration.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        self._validate_api_keys()
        self._validate_timeouts()
        self._validate_limits()
    
    def _validate_api_keys(self):
        """
        Ensure Google/Gemini API is configured and API key for authentication.
        
        Raises:
            ConfigurationError: If API keys are not configured
        """
        if not self.google_api_key:
            raise ConfigurationError(
                "GOOGLE_API_KEY must be configured for Gemini AI"
            )
        
        if not self.api_key:
            raise ConfigurationError(
                "API_KEY must be configured for authentication. "
                "Generate a secure random string and set it in environment variables."
            )
    
    def _validate_timeouts(self):
        """
        Validate timeout values.
        
        Raises:
            ConfigurationError: If timeouts are invalid
        """
        if self.api_timeout <= 0:
            raise ConfigurationError(
                f"API_TIMEOUT must be positive, got {self.api_timeout}"
            )
        
        if self.youtube_timeout <= 0:
            raise ConfigurationError(
                f"YOUTUBE_TIMEOUT must be positive, got {self.youtube_timeout}"
            )
        
        if self.api_timeout < 10:
            raise ConfigurationError(
                f"API_TIMEOUT too low ({self.api_timeout}s), minimum is 10s"
            )
    
    def _validate_limits(self):
        """
        Validate processing limits.
        
        Raises:
            ConfigurationError: If limits are invalid
        """
        if self.max_text_length <= 0:
            raise ConfigurationError(
                f"MAX_TEXT_LENGTH must be positive, got {self.max_text_length}"
            )
        
        if self.max_text_length > 100000:
            raise ConfigurationError(
                f"MAX_TEXT_LENGTH too large ({self.max_text_length}), "
                f"maximum is 100000"
            )
    
    @property
    def ai_provider(self) -> str:
        """Get the AI provider name."""
        return 'gemini'
    
    def to_dict(self) -> dict:
        """
        Export configuration as dictionary (for debugging/logging).
        
        Note: API keys are masked for security.
        """
        return {
            'google_configured': bool(self.google_api_key),
            'api_timeout': self.api_timeout,
            'youtube_timeout': self.youtube_timeout,
            'max_text_length': self.max_text_length,
            'debug': self.debug,
            'ai_provider': self.ai_provider
        }


# Singleton instance - validated on first import (Fail Fast)
try:
    config = Config()
except ConfigurationError as e:
    # Re-raise with additional context
    raise ConfigurationError(
        f"Application startup failed due to invalid configuration: {e.message}"
    ) from e
