"""
Controller for health check operations.
"""
from typing import Dict, Any
from app.config import config
from app.models import HealthResponse
from app.utils.logger import logger

class HealthController:
    def get_health_status(self) -> Dict[str, Any]:
        """Get application health status."""
        logger.debug("Health check")
        
        response = HealthResponse(
            version='2.0.0',
            sections=['transcript'],
            gemini_configured=bool(config.google_api_key),
            ai_provider=config.ai_provider
        )
        
        return response.to_dict()

