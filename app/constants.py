"""
Application-wide constants.
Centralizes all magic numbers, strings, and configuration values.
"""

# API Timeouts
YOUTUBE_API_TIMEOUT = 60
SUMMARIZATION_API_TIMEOUT = 120
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

# yt-dlp Configuration
YT_DLP_FORMAT = 'bestaudio/best'
YT_DLP_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
YT_DLP_FRAGMENT_RETRIES = 3
YT_DLP_SOCKET_TIMEOUT = 60

# Audio Processing
PREFERRED_AUDIO_CODEC = 'mp3'
PREFERRED_AUDIO_QUALITY = '128'

# Summary Types
VALID_SUMMARY_TYPES = ['concise', 'normal', 'detailed']
DEFAULT_SUMMARY_TYPE = 'normal'

# Token Limits by Summary Type
TOKEN_LIMITS = {
    'concise': 1000,
    'normal': 3000,
    'detailed': 4000
}

# Output Formats
VALID_OUTPUT_FORMATS = ['pdf', 'txt']
DEFAULT_OUTPUT_FORMAT = 'pdf'

# Logging Configuration
LOG_SEPARATOR = '=' * 80
LOG_SECTION_SEPARATOR = '-' * 40

# Cookie Configuration
COOKIES_FILENAME = 'cookies.txt'

# Error Messages
ERROR_NO_URL = 'No URL provided'
ERROR_NO_FILE = 'No file provided'
ERROR_INVALID_URL = 'Invalid YouTube URL'
ERROR_INVALID_FILE_TYPE = 'Only .txt files allowed'
ERROR_FILE_TOO_LARGE = 'File too large (max 5MB)'
ERROR_EMPTY_FILENAME = 'Empty filename'
ERROR_TRANSCRIPT_FAILED = 'Failed to generate transcript'
ERROR_SUMMARIZATION_FAILED = 'Failed to generate summary'
ERROR_NO_URL_OR_FILE = 'Provide either video URL or transcript file'

# Success Messages
SUCCESS_TRANSCRIPT_READY = 'Transcript ready'
SUCCESS_SUMMARY_READY = 'Summary ready'

# Prompts for Summarization (Polish)
SUMMARY_PROMPTS = {
    'concise': (
        "Jesteś ekspertem od syntezy informacji. Przeanalizuj poniższy transkrypt wideo YouTube. "
        "Stwórz **bardzo krótkie podsumowanie** (3-5 zdań). Skup się wyłącznie na **głównym wniosku** "
        "i najważniejszych faktach. Pomiń wstęp i zakończenie. Użyj **pogrubienia** dla kluczowych terminów."
    ),
    'normal': (
        "Jesteś profesjonalnym asystentem. Przeanalizuj transkrypt wideo. Stwórz przejrzyste podsumowanie "
        "(ok. 300-500 słów) w języku polskim. Struktura: 1. **Główny temat:** O czym jest wideo? (1-2 zdania). "
        "2. **Kluczowe punkty:** Lista punktowana (użyj myślników `-`). Każdy punkt powinien zawierać konkretną "
        "informację, a nie ogólnik. 3. **Wnioski / Actionable Advice:** Co z tego wynika dla widza? "
        "**Formatowanie:** Używaj **pogrubień** dla ważnych pojęć. Pisz stylem edukacyjnym i bezpośrednim."
    ),
    'detailed': (
        "Działasz jako zaawansowany analityk treści edukacyjnych. Przeanalizuj CAŁY dostarczony transkrypt wideo "
        "i przygotuj **kompleksowe opracowanie** (ok. 800-1000 słów) w języku polskim. **Wymagana struktura:** "
        "### 1. Wprowadzenie (Kontekst wideo i definicja problemu). ### 2. Szczegółowa Analiza (podzielona na "
        "sekcje tematyczne). Nie streszczaj chronologicznie, ale **tematycznie**. Wyodrębnij główne wątki jako "
        "nagłówki. Dla każdego wątku opisz szczegóły, dane, przykłady i argumenty autora. Używaj **pogrubień** "
        "dla terminologii. ### 3. Cytaty i Kluczowe Myśli (Przytocz lub sparafrazuj najważniejsze stwierdzenia). "
        "### 4. Podsumowanie i Wnioski Praktyczne (Synteza wiedzy, lista kroków/lekcji). **Styl:** Profesjonalny, "
        "akademicki lub ekspercki. Używaj poprawnego formatowania Markdown (nagłówki, listy, pogrubienia)."
    )
}

# Perplexity Configuration
PERPLEXITY_MODEL = "sonar-pro"
PERPLEXITY_TEMPERATURE = 0.7
PERPLEXITY_SYSTEM_PROMPT = (
    "You are a helpful assistant that creates high-quality summaries of video transcripts in Polish. "
    "Process the ENTIRE transcript provided and maintain important details."
)

# Gemini Configuration  
GEMINI_MODEL = "gemini-2.0-flash-exp"
GEMINI_TEMPERATURE = 0.7

# Format Detection Patterns
SPEAKER_REGEX_PATTERN = r'^(\[\d{1,2}:\d{2}(?::\d{2})?\])\s*(Speaker \d+|[\w\s]+):(.*)' 
TIMESTAMP_PATTERN = r'\[\d{1,2}:\d{2}(?::\d{2})?\]'
SEPARATOR_PATTERN = '=' * 20
