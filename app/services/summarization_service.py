"""
Summarization service utilities.
Handles text summarization using Perplexity and Gemini APIs.
"""
import requests
from typing import Optional, Dict

from app.config import config
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

class SummarizationService:
    """
    Service for text summarization.
    Encapsulates logic for interacting with multiple AI providers (Perplexity, Gemini).
    """

    def summarize(self, text: str, summary_type: str = DEFAULT_SUMMARY_TYPE) -> Optional[str]:
        """
        Summarize text using the next available provider.
        
        Args:
            text: Text to summarize
            summary_type: Type of summary (concise, normal, detailed)
            
        Returns:
            Summary text or None if all enabled providers fail
        """
        text = self._truncate_text(text)
        prompt = self._get_prompt(summary_type)
        max_tokens = self._get_max_tokens(summary_type)

        # 1. Try Perplexity if configured
        if config.use_perplexity:
            summary = self._summarize_with_perplexity(text, prompt, max_tokens)
            if summary:
                return summary
            logger.warning("Perplexity failed or returned bad response, trying fallback...")

        # 2. Try Gemini if configured (Fallback or Primary)
        if config.google_api_key:
            summary = self._summarize_with_gemini(text, prompt, max_tokens)
            if summary:
                return summary

        logger.error("All summarization providers failed.")
        return None

    def _truncate_text(self, text: str) -> str:
        if len(text) > MAX_TEXT_LENGTH:
            logger.warning(f"Truncating text from {len(text)} to {MAX_TEXT_LENGTH}")
            return text[:MAX_TEXT_LENGTH]
        return text

    def _get_prompt(self, summary_type: str) -> str:
        return SUMMARY_PROMPTS.get(summary_type, SUMMARY_PROMPTS[DEFAULT_SUMMARY_TYPE])

    def _get_max_tokens(self, summary_type: str) -> int:
        return TOKEN_LIMITS.get(summary_type, TOKEN_LIMITS[DEFAULT_SUMMARY_TYPE])

    def _summarize_with_perplexity(self, text: str, prompt: str, max_tokens: int) -> Optional[str]:
        try:
            logger.info("Perplexity API: Summarizing...")
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {config.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": PERPLEXITY_MODEL,
                "messages": [
                    {"role": "system", "content": PERPLEXITY_SYSTEM_PROMPT},
                    {"role": "user", "content": f"{prompt}\n\nTRANSKRYPT:\n\n{text}"}
                ],
                "max_tokens": max_tokens,
                "temperature": PERPLEXITY_TEMPERATURE
            }
            response = requests.post(url, headers=headers, json=payload, timeout=SUMMARIZATION_API_TIMEOUT)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
            
        except Exception as e:
            logger.error(f"Perplexity API error: {e}")
            return None

    def _summarize_with_gemini(self, text: str, prompt: str, max_tokens: int) -> Optional[str]:
        try:
            logger.info("Gemini API: Summarizing...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={config.google_api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": f"{prompt}\n\nTRANSKRYPT:\n\n{text}"}]}],
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": GEMINI_TEMPERATURE}
            }
            response = requests.post(url, headers=headers, json=payload, timeout=SUMMARIZATION_API_TIMEOUT)
            response.raise_for_status()
            return response.json()['candidates'][0]['content']['parts'][0]['text']
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None
