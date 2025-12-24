"""
Summarization service utilities.
Handles text summarization using Perplexity and Gemini APIs.
"""
import requests
from typing import Optional

from app.config import Config
from app.utils.logger import logger
from app.constants import (
    MAX_TEXT_LENGTH,
    SUMMARY_PROMPTS,
    TOKEN_LIMITS,
    SUMMARIZATION_API_TIMEOUT,
    PERPLEXITY_MODEL,
    PERPLEXITY_TEMPERATURE,
    PERPLEXITY_SYSTEM_PROMPT,
    GEMINI_MODEL,
    GEMINI_TEMPERATURE,
    DEFAULT_SUMMARY_TYPE
)


def truncate_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length allowed
        
    Returns:
        Truncated text
    """
    if len(text) > max_length:
        logger.warning(f"Truncating text from {len(text)} to {max_length} characters")
        return text[:max_length]
    return text


def get_prompt_for_type(summary_type: str) -> str:
    """
    Get summarization prompt for given type.
    
    Args:
        summary_type: Type of summary ('concise', 'normal', 'detailed')
        
    Returns:
        Prompt string
    """
    return SUMMARY_PROMPTS.get(summary_type, SUMMARY_PROMPTS[DEFAULT_SUMMARY_TYPE])


def get_max_tokens(summary_type: str) -> int:
    """
    Get maximum tokens for given summary type.
    
    Args:
        summary_type: Type of summary
        
    Returns:
        Maximum number of tokens
    """
    return TOKEN_LIMITS.get(summary_type, TOKEN_LIMITS[DEFAULT_SUMMARY_TYPE])


def summarize_with_perplexity(text: str, summary_type: str = DEFAULT_SUMMARY_TYPE) -> Optional[str]:
    """
    Summarize text using Perplexity API.
    
    Args:
        text: Text to summarize
        summary_type: Type of summary to generate
        
    Returns:
        Summary text or None if failed
    """
    try:
        logger.info(f"Perplexity API: summarizing ({summary_type} mode)...")
        
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {Config.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        text_to_summarize = truncate_text(text)
        prompt = get_prompt_for_type(summary_type)
        max_tokens = get_max_tokens(summary_type)
        
        payload = {
            "model": PERPLEXITY_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": PERPLEXITY_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\nTRANSKRYPT:\n\n{text_to_summarize}"
                }
            ],
            "max_tokens": max_tokens,
            "temperature": PERPLEXITY_TEMPERATURE
        }
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=SUMMARIZATION_API_TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        summary = result['choices'][0]['message']['content']
        logger.info(f"[OK] Perplexity response ({len(summary)} characters)")
        return summary
    
    except requests.exceptions.Timeout:
        logger.error("Perplexity API timeout")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Perplexity API request error: {str(e)}")
        return None
    except (KeyError, IndexError) as e:
        logger.error(f"Perplexity API response parsing error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Perplexity API error: {str(e)}")
        return None


def summarize_with_gemini(text: str, summary_type: str = DEFAULT_SUMMARY_TYPE) -> Optional[str]:
    """
    Summarize text using Gemini API.
    
    Args:
        text: Text to summarize
        summary_type: Type of summary to generate
        
    Returns:
        Summary text or None if failed
    """
    try:
        logger.info(f"Gemini API: summarizing ({summary_type} mode)...")
        
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{GEMINI_MODEL}:generateContent?key={Config.GOOGLE_API_KEY}"
        )
        headers = {"Content-Type": "application/json"}
        
        text_to_summarize = truncate_text(text)
        prompt = get_prompt_for_type(summary_type)
        max_tokens = get_max_tokens(summary_type)
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{prompt}\n\nTRANSKRYPT:\n\n{text_to_summarize}"
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": GEMINI_TEMPERATURE
            }
        }
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=SUMMARIZATION_API_TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        summary = result['candidates'][0]['content']['parts'][0]['text']
        logger.info(f"[OK] Gemini response ({len(summary)} characters)")
        return summary
    
    except requests.exceptions.Timeout:
        logger.error("Gemini API timeout")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Gemini API request error: {str(e)}")
        return None
    except (KeyError, IndexError) as e:
        logger.error(f"Gemini API response parsing error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        return None
