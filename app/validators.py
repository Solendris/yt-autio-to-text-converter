"""
Input validation utilities.
Provides validation functions for URLs, files, and other inputs.
"""
import os
import re
from typing import Tuple, Optional
from app.constants import (
    SUPPORTED_TRANSCRIPT_EXTENSIONS,
    MAX_UPLOAD_SIZE,
    ERROR_INVALID_URL,
    ERROR_INVALID_FILE_TYPE,
    ERROR_FILE_TOO_LARGE,
    ERROR_EMPTY_FILENAME
)


def validate_youtube_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if the URL is a valid YouTube URL.

    Args:
        url: The URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not url.strip():
        return False, ERROR_INVALID_URL

    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+'
    ]

    for pattern in youtube_patterns:
        if re.match(pattern, url.strip()):
            return True, None

    return False, ERROR_INVALID_URL


def validate_transcript_file(file) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded transcript file.

    Args:
        file: The uploaded file object

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file:
        return False, ERROR_EMPTY_FILENAME

    filename = file.filename
    if not filename or filename == '':
        return False, ERROR_EMPTY_FILENAME

    # Check file extension
    _, ext = os.path.splitext(filename)
    if ext.lower() not in SUPPORTED_TRANSCRIPT_EXTENSIONS:
        return False, ERROR_INVALID_FILE_TYPE

    # Check file size if possible
    if hasattr(file, 'content_length') and file.content_length:
        if file.content_length > MAX_UPLOAD_SIZE:
            return False, ERROR_FILE_TOO_LARGE

    return True, None



def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and invalid characters.
    
    Uses regex-based whitelist approach for maximum security.
    Addresses: High Vulnerability #10 - Path Traversal
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename
    """
    import re
    
    # Remove all characters except safe ones (alphanumeric, underscore, dash, dot)
    safe = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    
    # Remove multiple consecutive special characters
    safe = re.sub(r'_{2,}', '_', safe)
    safe = re.sub(r'\.{2,}', '.', safe)
    safe = re.sub(r'-{2,}', '-', safe)
    
    # Remove leading/trailing special characters
    safe = safe.strip('._- ')
    
    # Limit length to prevent filesystem issues
    if len(safe) > 255:
        import os
        name, ext = os.path.splitext(safe)
        safe = name[:255-len(ext)] + ext
    
    # Return safe filename or default
    return safe if safe else 'unnamed'
