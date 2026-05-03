#!/usr/bin/env bash
set -euo pipefail

echo "============================================"
echo " Your Everyday Tools - Dev Mode (macOS)"
echo "============================================"
echo

# --- Ensure venv exists ---
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

FLASK_PID=""

cleanup() {
    echo "Shutting down Flask..."
    if [ -n "$FLASK_PID" ] && kill -0 "$FLASK_PID" 2>/dev/null; then
        kill "$FLASK_PID" 2>/dev/null || true
        wait "$FLASK_PID" 2>/dev/null || true
    fi
    echo "Done."
}
trap cleanup EXIT

# --- Start Flask in dev mode (background) ---
echo "Starting Flask dev server on http://127.0.0.1:5000 ..."
python app.py &
FLASK_PID=$!

# --- Wait for Flask ---
echo "Waiting for Flask to be ready..."
for i in $(seq 1 15); do
    if curl -s http://127.0.0.1:5000/ > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# --- Ensure Electron deps ---
cd electron-wrapper
if [ ! -d "node_modules" ]; then
    echo "Installing Electron dependencies..."
    npm install
fi

# --- Start Electron ---
echo "Starting Electron..."
ELECTRON_WRAPPER=1 npx electron .
cd ..
