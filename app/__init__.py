from flask import Flask
from flask_cors import CORS
from app.config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)  # Enable CORS for all routes

    from app.routes import bp as api_bp
    app.register_blueprint(api_bp)

    @app.route('/')
    def index():
        return {"status": "ok", "message": "YouTube Summarizer Backend is running on Raspberry Pi"}

    return app
