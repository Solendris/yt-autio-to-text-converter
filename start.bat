@echo off
REM start.bat - Skrypt startowy dla Windows

echo Uruchamianie YouTube Summarizer...
echo.

REM Sprawdź czy virtual environment istnieje
if not exist "venv" (
    echo Virtual environment nie znaleziony!
    echo Tworze virtual environment...
    python -m venv venv
)

REM Aktywuj virtual environment
echo Aktywuje virtual environment...
call venv\Scripts\activate.bat

REM Sprawdź czy .env istnieje
if not exist ".env" (
    echo Plik .env nie znaleziony!
    echo Tworze .env z szablonu...
    copy .env.example .env
    echo WAZNE: Edytuj .env i dodaj swoje klucze API!
)

REM Zainstaluj/aktualizuj zależności
echo Instaluje zaleznosci...
pip install -r requirements.txt


REM Uruchom aplikację
echo.
echo Uruchamianie Flask serwera...
echo Frontend & Backend: http://localhost:5000
echo.

python run.py

pause
