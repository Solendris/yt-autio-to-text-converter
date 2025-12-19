import requests
from app.config import Config
from app.utils.logger import logger

def summarize_with_perplexity(text, summary_type="normal"):
    """SEKCJA 2: Podsumuj transkrypt za pomocą Perplexity API"""
    try:
        logger.info(f"Perplexity API: summarizing ({summary_type} mode)...")
        
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {Config.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        text_to_summarize = text[:20000] if len(text) > 20000 else text
        
        prompts = {
            "concise": "Podsumuj poniższy transkrypt w 3-5 zdaniach. Zachowaj GŁÓWNĄ MYŚL i kluczowe punkty. Bądź bardzo krótki i bezpośredni.",
            "normal": "Podsumuj poniższy transkrypt w ~300-500 słów. Zachowaj strukturę: Intro → Główne punkty → Wnioski. Używaj bullet points dla czytelności.",
            "detailed": "Podsumuj poniższy transkrypt w ~800-1000 słów. Zachowaj wszystkie ważne punkty, cytaty i przykłady. Strukturalizuj: Abstrakt → Sekcje → Analiza → Wnioski.",
        }
        
        prompt = prompts.get(summary_type, prompts["normal"])
        
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates high-quality summaries of video transcripts in Polish. Process the ENTIRE transcript provided and maintain important details."
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\nTRANSKRYPT:\n\n{text_to_summarize}"
                }
            ],
            "max_tokens": 3000,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        summary = result['choices'][0]['message']['content']
        logger.info(f"[OK] Perplexity response ({len(summary)} characters)")
        return summary
    
    except Exception as e:
        logger.error(f"Perplexity API error: {str(e)}")
        return None

def summarize_with_gemini(text, summary_type="normal"):
    """Fallback: Gemini API"""
    try:
        logger.info(f"Gemini API: summarizing ({summary_type} mode)...")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={Config.GOOGLE_API_KEY}"
        headers = {"Content-Type": "application/json"}
        
        text_to_summarize = text[:20000] if len(text) > 20000 else text
        
        prompts = {
            "concise": "Podsumuj w 3-5 zdaniach",
            "normal": "Podsumuj w ~300-500 słów z bullet points",
            "detailed": "Podsumuj w ~800-1000 słów ze wszystkimi szczegółami",
        }
        
        prompt = prompts.get(summary_type, prompts["normal"])
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{prompt}\n\nTRANSKRYPT:\n\n{text_to_summarize}"
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": 3000,
                "temperature": 0.7
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        summary = result['candidates'][0]['content']['parts'][0]['text']
        logger.info(f"[OK] Gemini response ({len(summary)} characters)")
        return summary
    
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        return None
