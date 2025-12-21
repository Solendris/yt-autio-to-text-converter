@echo off
REM start.bat - Skrypt startowy dla Windows (Backend + Frontend)

echo ==========================================
echo    YouTube Summarizer - Launcher
echo ==========================================
echo.

REM 1. Sprawdź Backend
echo [BACKEND] Sprawdzanie srodowiska...
if not exist "venv" (
    echo [BACKEND] Tworzenie virtual environment...
    python -m venv venv
)

REM 2. Aktywuj i zainstaluj zaleznosci backendu
echo [BACKEND] Instalacja zaleznosci...
call venv\Scripts\activate.bat
pip install -r requirements.txt

REM 3. Sprawdź Frontend
echo [FRONTEND] Sprawdzanie Node.js...
node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [BLAD] Node.js nie zostal znaleziony! 
    echo Zainstaluj Node.js z https://nodejs.org/ aby uruchomic frontend.
    pause
    exit /b
)

echo [FRONTEND] Instalacja zaleznosci (npm)...
cd frontend
call npm install
cd ..

REM 4. Uruchom oba moduły
echo.
echo [!] Uruchamiam aplikacje...
echo [!] Backend bedzie na: http://localhost:5000
echo [!] Frontend bedzie na: http://localhost:5173
echo.

REM Uruchom backend w nowym oknie
start "YouTube Summarizer - Backend (Flask)" cmd /k "call venv\Scripts\activate.bat && python run.py"

REM Uruchom frontend w tym oknie (lub nowym, jesli wolisz)
echo [VITE] Startowanie frontendu w tym oknie...
cd frontend
npm run dev

pause
