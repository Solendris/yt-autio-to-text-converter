# 🚀 Quick Start Guide (5 minut)

Najszybszy sposób na uruchomienie aplikacji.

## Krok 1: Przygotowanie (2 minuty)

```bash
# 1. Otwórz terminal/command prompt w folderze projektu

# 2. Utwórz virtual environment
python -m venv venv

# 3. Aktywuj
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Zainstaluj zależności (będzie trwać kilka minut!)
pip install -r requirements.txt
```

## Krok 2: Pobranie klucza API (1 minuta)

**Wybierz opcję A lub B:**

### Opcja A: Perplexity (ZALECANE - $5/miesiąc)

1. Przejdź na: https://www.perplexity.ai/settings/api
2. Zaloguj się / Utwórz konto
3. Kliknij "Generate API Key"
4. Skopiuj klucz

### Opcja B: Google Gemini (DARMOWE)

1. Przejdź na: https://aistudio.google.com/app/apikeys
2. Kliknij "Create API Key"
3. Skopiuj klucz

## Krok 3: Konfiguracja (1 minuta)

1. W folderze projektu utwórz plik `.env`
2. Wklej zawartość:

```
PERPLEXITY_API_KEY=your_key_here
GOOGLE_API_KEY=your_google_key_here
```

3. Zastąp `your_key_here` swoim kluczem (wystarczy jeden!)

## Krok 4: Uruchomienie (1 minuta)

**Terminal 1 - Backend:**
```bash
python app.py
```

Powinieneś zobaczyć:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

**Terminal 2 / Przeglądarka - Frontend:**

Opcja 1 (najprostsza):
```bash
# Otwórz plik index.html bezpośrednio w przeglądarce
```

Opcja 2 (jeśli wyżej nie zadziała):
```bash
# W nowym terminalu, w tym samym katalogu:
python -m http.server 8000

# Otwórz w przeglądarce:
http://localhost:8000/index.html
```

## ✅ To jest wszystko!

Teraz możesz:
1. Wkleić link do YouTube
2. Kliknąć "Generate PDF"
3. Pobrać podsumowanie

## 🐛 Jeśli coś nie działa

| Problem | Rozwiązanie |
|---------|------------|
| "Cannot connect to backend" | Sprawdź czy Flask uruchomiony (`python app.py`) |
| "Invalid API key" | Sprawdź czy klucz w `.env` jest poprawny |
| "Transcript not found" | To wideo nie ma dostępnych napisów |
| "Module not found" | Uruchom: `pip install -r requirements.txt` |

## 📚 Następne kroki

- Czytaj `README.md` aby zrozumieć wszystkie funcjonalności
- Sprawdź `app.py` aby zmodyfikować modele AI
- Dostosuj `index.html` aby zmienić wygląd

---

**Gotowe? Zacznij wklejać linki! 🎉**
