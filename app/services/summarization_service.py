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
        
        # Increase input limit (approx 25k-30k tokens for 100k chars)
        text_to_summarize = text[:100000] if len(text) > 100000 else text
        
        prompts = {
            "concise": "Jesteś ekspertem od syntezy informacji. Przeanalizuj poniższy transkrypt wideo YouTube. Stwórz **bardzo krótkie podsumowanie** (3-5 zdań). Skup się wyłącznie na **głównym wniosku** i najważniejszych faktach. Pomiń wstęp i zakończenie. Użyj **pogrubienia** dla kluczowych terminów.",
            "normal": "Jesteś profesjonalnym asystentem. Przeanalizuj transkrypt wideo. Stwórz przejrzyste podsumowanie (ok. 300-500 słów) w języku polskim. Struktura: 1. **Główny temat:** O czym jest wideo? (1-2 zdania). 2. **Kluczowe punkty:** Lista punktowana (użyj myślników `-`). Każdy punkt powinien zawierać konkretną informację, a nie ogólnik. 3. **Wnioski / Actionable Advice:** Co z tego wynika dla widza? **Formatowanie:** Używaj **pogrubień** dla ważnych pojęć. Pisz stylem edukacyjnym i bezpośrednim.",
            "detailed": "Działasz jako zaawansowany analityk treści edukacyjnych. Przeanalizuj CAŁY dostarczony transkrypt wideo i przygotuj **kompleksowe opracowanie** (1500-2500 słów) w języku polskim. **Wymagana struktura:** ### 1. Wprowadzenie (Kontekst wideo i definicja problemu). ### 2. Szczegółowa Analiza (podzielona na sekcje tematyczne). Nie streszczaj chronologicznie, ale **tematycznie**. Wyodrębnij główne wątki jako nagłówki. Dla każdego wątku opisz szczegóły, dane, przykłady i argumenty autora. Używaj **pogrubień** dla terminologii. ### 3. Cytaty i Kluczowe Myśli (Przytocz lub sparafrazuj najważniejsze stwierdzenia). ### 4. Podsumowanie i Wnioski Praktyczne (Synteza wiedzy, lista kroków/lekcji). **Styl:** Profesjonalny, akademicki lub ekspercki. Używaj poprawnego formatowania Markdown (nagłówki, listy, pogrubienia). Twoim celem jest to, aby użytkownik nie musiał oglądać wideo po przeczytaniu tej notatki.",
        }
        
        prompt = prompts.get(summary_type, prompts["normal"])
        
        # Adjust max_tokens based on summary type
        max_tokens_map = {
            "concise": 1000,
            "normal": 3000,
            "detailed": 8000
        }
        
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
            "max_tokens": max_tokens_map.get(summary_type, 3000),
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
        
        text_to_summarize = text[:100000] if len(text) > 100000 else text
        
        prompts = {
            "concise": "Jesteś ekspertem od syntezy informacji. Przeanalizuj poniższy transkrypt wideo YouTube. Stwórz **bardzo krótkie podsumowanie** (3-5 zdań). Skup się wyłącznie na **głównym wniosku** i najważniejszych faktach. Pomiń wstęp i zakończenie. Użyj **pogrubienia** dla kluczowych terminów.",
            "normal": "Jesteś profesjonalnym asystentem. Przeanalizuj transkrypt wideo. Stwórz przejrzyste podsumowanie (ok. 300-500 słów) w języku polskim. Struktura: 1. **Główny temat:** O czym jest wideo? (1-2 zdania). 2. **Kluczowe punkty:** Lista punktowana (użyj myślników `-`). Każdy punkt powinien zawierać konkretną informację, a nie ogólnik. 3. **Wnioski / Actionable Advice:** Co z tego wynika dla widza? **Formatowanie:** Używaj **pogrubień** dla ważnych pojęć. Pisz stylem edukacyjnym i bezpośrednim.",
            "detailed": "Działasz jako zaawansowany analityk treści edukacyjnych. Przeanalizuj CAŁY dostarczony transkrypt wideo i przygotuj **kompleksowe opracowanie** (1500-2500 słów) w języku polskim. **Wymagana struktura:** ### 1. Wprowadzenie (Kontekst wideo i definicja problemu). ### 2. Szczegółowa Analiza (podzielona na sekcje tematyczne). Nie streszczaj chronologicznie, ale **tematycznie**. Wyodrębnij główne wątki jako nagłówki. Dla każdego wątku opisz szczegóły, dane, przykłady i argumenty autora. Używaj **pogrubień** dla terminologii. ### 3. Cytaty i Kluczowe Myśli (Przytocz lub sparafrazuj najważniejsze stwierdzenia). ### 4. Podsumowanie i Wnioski Praktyczne (Synteza wiedzy, lista kroków/lekcji). **Styl:** Profesjonalny, akademicki lub ekspercki. Używaj poprawnego formatowania Markdown (nagłówki, listy, pogrubienia). Twoim celem jest to, aby użytkownik nie musiał oglądać wideo po przeczytaniu tej notatki.",
        }
        
        prompt = prompts.get(summary_type, prompts["normal"])
        
        # Adjust max_tokens based on summary type
        max_tokens_map = {
            "concise": 1000,
            "normal": 3000,
            "detailed": 8000
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{prompt}\n\nTRANSKRYPT:\n\n{text_to_summarize}"
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens_map.get(summary_type, 3000),
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
