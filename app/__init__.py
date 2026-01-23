from flask import Flask
from flask_cors import CORS
from app.exceptions import ConfigurationError
from app.utils.logger import logger


def create_app(config_class=None):
    """
    Application factory.
    
    This function creates and configures the Flask application,
    implementing Fail Fast by validating configuration on startup.
    
    Args:
        config_class: Configuration class (optional, for testing)
        
    Returns:
        Configured Flask application
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    app = Flask(__name__)
    
    # Set global upload size limit
    # Addresses: High Vulnerability #7 - Lack of Upload Size Validation
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB
    
    # Fail Fast: Validate configuration on startup
    try:
        from app.config import config
        logger.info("Configuration validated successfully")
        logger.info(f"AI Provider: {config.ai_provider}")
        
        # Store config in app for access in routes
        app.config['APP_CONFIG'] = config
        
    except ConfigurationError as e:
        logger.error(f"Configuration validation failed: {e.message}")
        raise
    
    # Configure CORS with whitelist
    # Addresses: Critical Vulnerability #2 - Unrestricted CORS
    # Note: Include both with and without trailing slash - browsers vary
    allowed_origins = [
        "https://solendris.github.io",   # Production frontend
        "https://solendris.github.io/",  # Production frontend (with trailing slash)
        "http://localhost:5173",         # Local development
        "http://127.0.0.1:5173"          # Alternative localhost
    ]
    
    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-API-Key", "ngrok-skip-browser-warning"],
            "expose_headers": ["Content-Type"],
            "supports_credentials": False,
            "max_age": 3600
        }
    })
    logger.info(f"CORS enabled for origins: {', '.join(allowed_origins)}")
    
    # Register error handlers
    from app.middleware.error_handler import init_middleware
    init_middleware(app)
    
    # Register blueprints
    from app.routes import bp as api_bp
    app.register_blueprint(api_bp)
    logger.info("API blueprint registered")
    
    @app.route('/')
    def index():
        """Root endpoint - health check."""
        return {
            "status": "ok",
            "message": "YouTube Summarizer Backend is running",
            "version": "2.0.0"
        }
    
    # Add security headers to all responses
    @app.after_request
    def add_security_headers(response):
        """Add security headers to prevent common vulnerabilities."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    logger.info("Flask application created successfully")
    return app
