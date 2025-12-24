import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration with validation."""
    
    # API Keys
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '').strip()
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '').strip()
    
    # Feature Flags
    USE_PERPLEXITY = PERPLEXITY_API_KEY != ''
    
    # Timeout Configuration (in seconds)
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '120'))
    YOUTUBE_TIMEOUT = int(os.getenv('YOUTUBE_TIMEOUT', '60'))
    
    # Processing Limits
    MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', '20000'))
    
    # Debug Mode
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not cls.GOOGLE_API_KEY and not cls.PERPLEXITY_API_KEY:
            raise ValueError(
                "At least one API key must be configured: "
                "GOOGLE_API_KEY or PERPLEXITY_API_KEY"
            )
        
        if cls.API_TIMEOUT <= 0:
            raise ValueError("API_TIMEOUT must be positive")
        
        if cls.YOUTUBE_TIMEOUT <= 0:
            raise ValueError("YOUTUBE_TIMEOUT must be positive")
        
        return True
