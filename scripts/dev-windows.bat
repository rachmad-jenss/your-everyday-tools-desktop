@echo off
setlocal

echo ============================================
echo  Your Everyday Tools - Dev Mode (Windows)
echo ============================================
echo.

REM --- Ensure venv exists ---
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    pip install waitress
) else (
    call venv\Scripts\activate.bat
)

REM --- Start Flask in dev mode (background) ---
echo Starting Flask dev server on http://127.0.0.1:5000 ...
start "Flask Dev Server" cmd /c "call venv\Scripts\activate.bat && python app.py"

REM --- Wait for Flask to start ---
echo Waiting for Flask to be ready...
timeout /t 3 /nobreak >nul

REM --- Start Electron pointing to dev server ---
echo Starting Electron...
cd electron-wrapper
if not exist node_modules (
    echo Installing Electron dependencies...
    call npm install
)
set ELECTRON_WRAPPER=1
call npx electron .
cd ..

REM --- When Electron closes, kill Flask ---
echo Shutting down Flask...
taskkill /fi "WINDOWTITLE eq Flask Dev Server" /f >nul 2>&1
echo Done.
