import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from app.config import Config


def create_app(config_class=Config):
    app = Flask(__name__, static_folder='../dist', static_url_path='/')
    app.config.from_object(config_class)

    CORS(app)  # Enable CORS for all routes

    from app.routes import bp as api_bp
    app.register_blueprint(api_bp)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

    return app
