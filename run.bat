@echo off
setlocal

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo   Python 3.10 or newer is required, but was not found on PATH.
    echo.
    echo   Download and install it from:
    echo       https://www.python.org/downloads/
    echo.
    echo   During install, make sure to check "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo   First-time setup: creating virtual environment...
    echo   (this only happens once and takes about a minute)
    echo.
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo   Failed to create the virtual environment.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"

echo.
echo   Checking dependencies...
pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo.
    echo   Dependency install failed. Check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo   ============================================================
echo     EveryTools is starting at http://localhost:5000
echo     Your browser will open automatically in a moment.
echo     Close this window to stop the server.
echo   ============================================================
echo.

start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5000"
python app.py

pause
