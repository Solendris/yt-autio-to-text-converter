# YouTube Video Summarizer

Zaawansowana aplikacja do automatycznego pobierania transkrypcji z YouTube, generowania profesjonalnych podsumowań przy użyciu AI (Perplexity/Gemini) i eksportu do estetycznych plików PDF.

## Kluczowe Funkcje

- **Dwa Niezależne Moduły**: Oddzielne sekcje do pobierania samego transkryptu (TXT) i generowania podsumowań.
- **Dual AI Engine**:
  - **Perplexity AI** (Sonar Pro): Domyślny, wysokiej jakości model do analizy.
  - **Google Gemini**: Automatyczny fallback w przypadku problemów z Perplexity.
- **Profesjonalne PDF**:
  - **Pełne wsparcie dla języka polskiego** (czcionka Lato).
  - **Formatowanie Markdown**: Pogrubienia, listy wypunktowane, nagłówki.
  - **Metadane**: Prawdziwy tytuł wideo w dokumencie (zamiast URL).
- **Tryb Hybrydowy**: Generowanie jednego pliku PDF zawierającego zarówno podsumowanie, jak i pełny transkrypt.
- **Inteligentne Pobieranie**:
  - Automatyczne wykrywanie napisów (YouTube API).
  - Fallback do **Whisper** (mowa na tekst) jeśli napisy nie są dostępne.

## Wymagania

- System: Windows / macOS / Linux
- Python 3.8+
- [FFmpeg](https://ffmpeg.org/) (wymagany do działania Whisper)
- Klucze API:
  - **Perplexity AI** (wymagany do działania domyślnego)
  - **Google Gemini** (opcjonalny, jako zapasowy)

## Instalacja i Konfiguracja

### 1. Pobierz projekt
Pobierz kod źródłowy i rozpakuj w wybranym folderze.

### 2. Utwórz środowisko (opcjonalne, ale zalecane)
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Zainstaluj zależności
```bash
pip install -r requirements.txt
```
*Uwaga: Pierwsza instalacja `faster-whisper` może chwilę potrwać.*

### 4. Skonfiguruj klucze API
Utwórz plik `.env` w głównym katalogu (obok `run.py`) i wklej swoje klucze:
```ini
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxx
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxx  # Opcjonalnie
```

## Uruchamianie

Najprostszy sposób (Windows):
Uruchom plik **`start.bat`**.
*Automatycznie aktywuje środowisko, instaluje braki i startuje serwer.*

Metoda ręczna:
```bash
python run.py
```

Aplikacja dostępna pod adresem: **http://localhost:5000**

## Instrukcja Obsługi

### Sekcja 1: Pobierz Transkrypt
1. Wklej link do wideo YouTube.
2. Kliknij **Generate Transcript**.
3. Pobierz surowy plik `.txt`.

### Sekcja 2: Generuj Podsumowanie
1. Wybierz źródło: **From Video** (URL) lub **From File** (wgraj swój .txt).
2. Wybierz typ podsumowania:
   - **Concise**: Krótka esencja (3-5 zdań).
   - **Normal**: Standardowe podsumowanie (kluczowe punkty, wnioski).
   - **Detailed**: Bardzo szczegółowe opracowanie (analiza tematyczna, bez zbędnych wstępów).
3. Kliknij **Generate Summary**.
4. Gotowy PDF (lub TXT) pobierze się automatycznie.

### Sekcja Hybrydowa
1. Wklej link URL.
2. Kliknij **Generate Hybrid PDF**.
3. Otrzymasz dokument zawierający na początku podsumowanie, a na kolejnych stronach pełny transkrypt.

## Rozwiązywanie Problemów

- **Błąd "FFmpeg not found"**: Upewnij się, że FFmpeg jest zainstalowany i dodany do zmiennej środowiskowej PATH.
- **Czarne kwadraty zamiast polskich znaków**: Zostało to naprawione w tej wersji dzięki czcionce Lato. Jeśli problem występuje, upewnij się, że folder `app/static/fonts` zawiera pliki `.ttf`.
- **Timeout przy długich wideo**: Dla bardzo długich materiałów (>1h) proces może trwać dłużej niż 120s. Spróbuj użyć trybu "Concise" lub podzielić materiał.

## Licencja
Projekt na użytek własny / edukacyjny.
