from flask import Flask, render_template
from flask_cors import CORS
from app.config import Config

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)
    
    CORS(app) # Enable CORS for all routes

    from app.routes import bp as api_bp
    app.register_blueprint(api_bp)
    
    @app.route('/')
    def index():
        return render_template('index.html')
        
    @app.route('/index.html') # Legacy support
    def index_legacy():
        return render_template('index.html')
    
    return app
