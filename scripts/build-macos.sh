#!/usr/bin/env bash
set -euo pipefail

echo "============================================"
echo " Your Everyday Tools - macOS Build Script"
echo "============================================"
echo

# --- Step 1: Python venv and dependencies ---
echo "[1/5] Creating Python virtual environment..."
rm -rf venv
python3 -m venv venv
source venv/bin/activate

echo "[2/5] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller gunicorn

# --- Step 2: PyInstaller build ---
echo "[3/5] Building backend with PyInstaller..."
pyinstaller your-everyday-tools.spec --clean --noconfirm

# --- Step 3: Copy backend binary to Electron resources ---
echo "[4/5] Copying backend to Electron wrapper..."
rm -rf electron-wrapper/resources/backend
cp -R dist/YourEverydayTools electron-wrapper/resources/backend
chmod +x electron-wrapper/resources/backend/YourEverydayTools

# --- Step 4: Build Electron installer ---
echo "[5/5] Building Electron installer..."
cd electron-wrapper
npm install
npm run build-mac
cd ..

echo
echo "============================================"
echo " Build complete!"
echo " DMG: electron-wrapper/dist/"
echo "============================================"
echo
echo "NOTE: For distribution, set these env vars for code signing:"
echo "  export CSC_LINK=/path/to/certificate.p12"
echo "  export CSC_KEY_PASSWORD=your-password"
echo "Then re-run this script."
