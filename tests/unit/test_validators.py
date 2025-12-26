import pytest
from app.validators import (
    validate_youtube_url,
    validate_transcript_file,
    validate_summary_type,
    validate_output_format
)
from app.constants import VALID_SUMMARY_TYPES, VALID_OUTPUT_FORMATS

class TestValidators:
    @pytest.mark.parametrize("url,is_valid", [
        ("https://www.youtube.com/watch?v=abcdefghijk", True),
        ("https://youtu.be/abcdefghijk", True),
        ("https://www.youtube.com/watch?v=abcdefghijk&t=10s", True),
        ("invalid_url", False),
        ("http://google.com", False),
        ("", False),
    ])
    def test_validate_youtube_url(self, url, is_valid):
        result, error = validate_youtube_url(url)
        assert result == is_valid

    def test_validate_summary_type(self):
        for summary_type in VALID_SUMMARY_TYPES:
            assert validate_summary_type(summary_type) == summary_type
        assert validate_summary_type("invalid_type") == "normal" # Default

    def test_validate_output_format(self):
        for fmt in VALID_OUTPUT_FORMATS:
            assert validate_output_format(fmt) == fmt
        assert validate_output_format("doc") == "pdf" # Default

    def test_validate_transcript_file_valid(self, tmp_path):
        # Create a dummy txt file
        p = tmp_path / "test.txt"
        p.write_text("content")
        
        # Mocking werkzeug FileStorage is tricky without dependency, 
        # so we'll skip complex file validation here or mock basic attributes
        class MockFile:
            filename = "test.txt"
            def seek(self, pos, whence=0): pass
            def tell(self): return 7 # Size < MAX
        
        valid, msg = validate_transcript_file(MockFile())
        assert valid is True

    def test_validate_transcript_file_invalid_ext(self):
        class MockFile:
            filename = "test.pdf" # Invalid extension for input
            def seek(self, pos, whence=0): pass
            def tell(self): return 0

        valid, msg = validate_transcript_file(MockFile())
        assert valid is False
