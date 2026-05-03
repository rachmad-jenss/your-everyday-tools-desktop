@echo off
setlocal enabledelayedexpansion

echo ============================================
echo  Your Everyday Tools - Windows Build Script
echo ============================================
echo.

REM --- Step 1: Python venv and dependencies ---
echo [1/5] Creating Python virtual environment...
if exist venv rmdir /s /q venv
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create venv. Is Python installed?
    exit /b 1
)

echo [2/5] Installing Python dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller waitress
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    exit /b 1
)

REM --- Step 2: PyInstaller build ---
echo [3/5] Building backend with PyInstaller...
pyinstaller your-everyday-tools.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    exit /b 1
)

REM --- Step 3: Copy backend binary to Electron resources ---
echo [4/5] Copying backend to Electron wrapper...
if not exist electron-wrapper\resources\backend mkdir electron-wrapper\resources\backend
xcopy /E /I /Y dist\YourEverydayTools electron-wrapper\resources\backend
if errorlevel 1 (
    echo ERROR: Could not copy backend files.
    exit /b 1
)

REM --- Step 4: Build Electron installer ---
echo [5/5] Building Electron installer...
cd electron-wrapper
call npm install
if errorlevel 1 (
    echo ERROR: npm install failed.
    exit /b 1
)
call npm run build-win
if errorlevel 1 (
    echo ERROR: Electron build failed.
    exit /b 1
)
cd ..

echo.
echo ============================================
echo  Build complete!
echo  Installer: electron-wrapper\dist\
echo ============================================
echo.
echo NOTE: The .exe may be flagged by antivirus.
echo Consider code-signing with a trusted certificate
echo for production distribution.
