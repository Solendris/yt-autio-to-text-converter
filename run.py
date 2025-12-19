from app import create_app
from app.utils.logger import logger

app = create_app()

if __name__ == '__main__':
    logger.info("Starting Flask server...")
    logger.info("Frontend: http://localhost:5000/index.html")
    logger.info("Endpoints:")
    logger.info("  - POST /api/transcript")
    logger.info("  - POST /api/summarize")
    logger.info("  - POST /api/hybrid")
    app.run(debug=True, port=5000)
