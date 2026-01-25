import pytest
from app import create_app
from app.config import Config

class TestConfig(Config):
    TESTING = True
    DEBUG = True
    GOOGLE_API_KEY = "test_google_key"

@pytest.fixture
def app():
    app = create_app(TestConfig)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_youtube(mocker):
    """Mock the YouTube service functions used in routes."""
    return {
        'get_transcript': mocker.patch('app.routes.get_transcript'),
        'get_diarized_transcript': mocker.patch('app.routes.get_diarized_transcript'),
        'extract_video_id': mocker.patch('app.routes.extract_video_id'),
        'get_video_title': mocker.patch('app.routes.get_video_title'),
    }


