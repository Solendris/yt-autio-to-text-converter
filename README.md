# 📺 YouTube Video Summarizer

Aplikacja internetowa, która automatycznie pobiera transkrypcje filmów YouTube i generuje ich podsumowania w formacie PDF przy użyciu sztucznej inteligencji (Perplexity AI lub Google Gemini).

## ✨ Cechy

- ✅ Pobieranie transkrypcji z YouTube (native captions)
- ✅ Fallback: Konwersja mowy na tekst (Faster Whisper - open source)
- ✅ Generowanie podsumowań AI (Perplexity lub Gemini)
- ✅ Eksport do PDF z formatowaniem
- ✅ Prosty, responsywny frontend
- ✅ Backend w Pythonie (Flask)

## 🛠️ Wymagania

- Python 3.8+
- pip (menadżer pakietów Python)
- Konto Perplexity AI (z kredytami API) LUB Google Gemini API key

## 📋 Instalacja

### 1. Klonuj lub pobierz projekt

```bash
# Utwórz folder projektu
mkdir youtube-summarizer
cd youtube-summarizer
```

### 2. Zainstaluj zależności

```bash
# Utwórz virtual environment (opcjonalnie ale zalecane)
python -m venv venv

# Aktywuj virtual environment
# Na Windows:
venv\Scripts\activate
# Na macOS/Linux:
source venv/bin/activate

# Zainstaluj pakiety
pip install -r requirements.txt
```

**Ważne**: Instalacja `faster-whisper` może potrwać kilka minut przy pierwszym uruchomieniu.

### 3. Skonfiguruj zmienne środowiskowe

1. Utwórz plik `.env` w głównym katalogu projektu
2. Skopiuj zawartość z `.env.example`
3. Dodaj swoje klucze API

#### Pobranie Perplexity API Key:
1. Przejdź na https://www.perplexity.ai/settings/api
2. Zaloguj się lub utwórz konto
3. Przejdź do sekcji API Settings
4. Wygeneruj nowy API key
5. Skopiuj do `.env` jako `PERPLEXITY_API_KEY`

#### Pobranie Google Gemini API Key (fallback):
1. Przejdź na https://aistudio.google.com/app/apikeys
2. Kliknij "Create API Key"
3. Skopiuj do `.env` jako `GOOGLE_API_KEY`

### 4. Uruchom aplikację

```bash
# Uruchom backend Flask
python app.py
```

Backend będzie dostępny na `http://localhost:5000`

### 5. Otwórz frontend

1. Otwórz plik `index.html` w przeglądarce (lub serwuj go na localhost)
2. Jeśli chcesz serwować lokalnie:
   ```bash
   # Python 3
   python -m http.server 8000
   ```
   Potem otwórz `http://localhost:8000/index.html`

## 🚀 Użycie

1. **Wklej link do YouTube**:
   - Obsługiwane formaty:
     - https://www.youtube.com/watch?v=...
     - https://youtu.be/...
     - https://www.youtube.com/embed/...

2. **(Opcjonalnie) Testuj transkrypcję**:
   - Kliknij "Test Transcript" aby sprawdzić czy wideo ma dostępne napisy
   - Zobaczysz fragment transkrypcji

3. **Generuj PDF**:
   - Kliknij "Generate PDF"
   - Czekaj (może potrwać 1-2 minuty)
   - PDF zostanie automatycznie pobrany

## 📁 Struktura projektu

```
youtube-summarizer/
├── app.py                 # Backend Flask
├── index.html            # Frontend HTML/CSS/JS
├── requirements.txt      # Python dependencies
├── .env.example         # Template zmiennych środowiskowych
└── README.md            # Ta instrukcja
```

## 🔍 Szczegóły techniczne

### Backend (Python + Flask)

- **youtube-transcript-api**: Pobieranie transkrypcji z YouTube
- **faster-whisper**: Open-source konwersja mowy→tekst (fallback)
- **reportlab**: Generowanie PDF-ów
- **requests**: Komunikacja z API Perplexity i Gemini

### Frontend (HTML + CSS + JS)

- Vanilla JavaScript (bez frameworks)
- Responsywny design
- Real-time status updates
- Download automatyczny PDF-ów

### API Endpoints

#### GET `/api/health`
Sprawdza status aplikacji i dostępne AI providers.

**Response:**
```json
{
  "status": "ok",
  "perplexity_configured": true,
  "gemini_configured": true,
  "ai_provider": "perplexity"
}
```

#### POST `/api/test-transcript`
Testuje pobranie transkrypcji bez generowania podsumowania.

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=..."
}
```

**Response:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "transcript_length": 5000,
  "transcript_preview": "Today we're going to talk about...",
  "source": "youtube"
}
```

#### POST `/api/summarize`
Główny endpoint - pobiera transkrypcję i generuje podsumowanie.

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "title": "Optional video title"
}
```

**Response:** PDF file

## ⚙️ Konfiguracja zaawansowana

### Zmiana modelu Whisper

W `app.py` znaldzień linia:
```python
whisper_model = WhisperModel("base", device="cpu", compute_type="float32")
```

Dostępne modele: `tiny`, `small`, `base`, `medium`, `large`
- Mniejsze = szybciej, mniej dokładnie
- Większe = wolniej, bardziej dokładnie

### Zmiana modelu Perplexity

W `app.py`:
```python
"model": "sonar-pro",  # Zmień na "sonar-medium-online" dla szybszych odpowiedzi
```

Dostępne modele:
- `sonar-pro`: Najlepszej jakości (wolniejsze)
- `sonar-medium-online`: Szybsze (mniej dokładne)

## 🐛 Troubleshooting

### "Backend not reachable"
- Sprawdź czy Flask jest uruchomiony (`python app.py`)
- Sprawdź czy uruchamiasz na `localhost:5000`
- Sprawdź konsolę Flask pod kątem błędów

### "Nie udało się pobrać transkrypcji"
- Wideo może nie mieć dostępnych napisów
- YouTube może wymagać autoryzacji
- Spróbuj innego wideo

### "API Error - Invalid key"
- Sprawdź czy klucz API w `.env` jest poprawny
- Upewnij się że .env jest w głównym katalogu
- Zrestartuj Flask (`python app.py`)

### "Whisper model download issue"
- Pierwszy start ściąga model (może potrwać)
- Sprawdź połączenie internetowe
- Spróbuj uruchomić ponownie

### Aplikacja działa bardzo wolno
- Wyłącz Whisper fallback (zawsze pobieraj transkrypcje z YouTube)
- Zmień na mniejszy model Whisper (`tiny`)
- Zmień AI model na szybszy (`sonar-medium-online`)

## 📊 Limity i koszty

### Perplexity API ($5/miesiąc starter)
- ~2500-5000 znaków = 1 podsumowanie
- Szacunek: 30-50 podsumowań za $5

### Google Gemini API (free tier dostępny)
- Free tier: 60 request/minuta
- Unlimited queries za darmo

### YouTube Transcript API
- **Bezpłatne** - brak limitów

### Faster Whisper
- **Bezpłatne** - działa lokalnie

## 🔐 Bezpieczeństwo

⚠️ **WAŻNE**: 
- Nigdy nie umieszczaj `.env` w repozytorium Git
- `.env` zawiera wrażliwe dane (klucze API)
- Dodaj `.env` do `.gitignore` jeśli commitujesz kod

## 🚀 Deployment na serwer

Aby wdrożyć na produkcji:

1. **Użyj WSGI server**:
   ```bash
   pip install gunicorn
   gunicorn app:app
   ```

2. **Ustaw zmienne środowiskowe na serwerze** (np. Heroku, AWS, DigitalOcean)

3. **Obsłuż HTTPS i CORS** odpowiednio

4. **Skaluj Whisper** (może używać dużo RAM na CPU)

## 📝 Licencja

Ten projekt jest na licencji MIT. Możesz go swobodnie używać i modyfikować.

## 🤝 Kontakt i wsparcie

Jeśli masz pytania:
- Sprawdź console przeglądarki (F12 → Console) pod kątem błędów JS
- Sprawdź terminal Flask pod kątem błędów Python
- Upewnij się że wszystkie API keys są poprawne

## 📚 Przydatne linki

- [Perplexity API Docs](https://docs.perplexity.ai)
- [Google Gemini API Docs](https://ai.google.dev)
- [YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api)
- [Faster Whisper](https://github.com/SYSTRAN/faster-whisper)
- [Flask Documentation](https://flask.palletsprojects.com)

---

**Miłego korzystania z YouTube Summarizer! 🎉**
