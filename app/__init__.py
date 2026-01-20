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
    
    # Enable CORS
    CORS(app)
    logger.info("CORS enabled for all routes")
    
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
    
    logger.info("Flask application created successfully")
    return app
