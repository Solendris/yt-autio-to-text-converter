"""
Application-wide constants.
Centralizes all magic numbers, strings, and configuration values.
"""

# API Timeouts
YOUTUBE_API_TIMEOUT = 60
DEBUG_ENDPOINT_TIMEOUT = 30

# Text Processing Limits
MAX_TEXT_LENGTH = 20000
TRANSCRIPT_PREVIEW_LENGTH = 200

# Retry Configuration
MAX_DOWNLOAD_ATTEMPTS = 3
DOWNLOAD_RETRY_DELAY = 5  # seconds

# File Configuration
SUPPORTED_TRANSCRIPT_EXTENSIONS = ['.txt']
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB

# Security Configuration
MAX_VIDEO_DURATION = 5400  # 1.5 hours in seconds
OPERATION_TIMEOUT = 300  # 5 minutes for long-running operations
RATE_LIMIT_REQUESTS = 50  # Maximum requests per hour
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds

# yt-dlp Configuration
YT_DLP_FORMAT = 'ba/best'
YT_DLP_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
YT_DLP_FRAGMENT_RETRIES = 3
YT_DLP_SOCKET_TIMEOUT = 60

# Audio Processing
PREFERRED_AUDIO_CODEC = 'mp3'
PREFERRED_AUDIO_QUALITY = '128'

# Logging Configuration
LOG_SEPARATOR = '=' * 80
LOG_SECTION_SEPARATOR = '-' * 40

# Cookie Configuration
COOKIES_FILENAME = 'cookies.txt'

# Error Messages
ERROR_NO_FILE = 'No file provided'
ERROR_INVALID_URL = 'Invalid YouTube URL'
ERROR_INVALID_FILE_TYPE = 'Only .txt files allowed'
ERROR_FILE_TOO_LARGE = 'File too large (max 5MB)'
ERROR_EMPTY_FILENAME = 'Empty filename'
ERROR_TRANSCRIPT_FAILED = 'Failed to generate transcript'

# Success Messages
SUCCESS_TRANSCRIPT_READY = 'Transcript ready'

# Gemini Configuration
GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_TEMPERATURE = 0.7

# Format Detection Patterns
SPEAKER_REGEX_PATTERN = r'^(\[\d{1,2}:\d{2}(?::\d{2})?\])\s*(Speaker \d+|[\w\s]+):(.*)'
TIMESTAMP_PATTERN = r'\[\d{1,2}:\d{2}(?::\d{2})?\]'
SEPARATOR_PATTERN = '=' * 20

