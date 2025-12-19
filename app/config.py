import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '').strip()
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '').strip()
    USE_PERPLEXITY = PERPLEXITY_API_KEY != ''
