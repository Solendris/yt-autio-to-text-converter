import pytest
from app import create_app
from app.config import Config

class TestConfig(Config):
    TESTING = True
    DEBUG = True
    PERPLEXITY_API_KEY = "test_pplx_key"
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

@pytest.fixture
def mock_summarizer(mocker):
    """Mock the summarization service functions used in routes."""
    return {
        'summarize_with_perplexity': mocker.patch('app.routes.summarize_with_perplexity'),
        'summarize_with_gemini': mocker.patch('app.routes.summarize_with_gemini'),
    }

@pytest.fixture
def mock_pdf(mocker):
    """Mock PDF generation."""
    return {
        'create_pdf_summary': mocker.patch('app.routes.create_pdf_summary'),
        'create_hybrid_pdf': mocker.patch('app.routes.create_hybrid_pdf')
    }
