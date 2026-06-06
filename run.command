#!/usr/bin/env bash
# Double-click launcher for macOS. Also used by run.sh on Linux.

set -u
cd "$(dirname "$0")"

find_python() {
    for cmd in python3 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            if "$cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
                printf '%s\n' "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

PYTHON_CMD="$(find_python || true)"

if [ -z "$PYTHON_CMD" ]; then
    echo
    echo "  Python 3.10 or newer is required, but was not found."
    echo
    echo "  macOS: install Python from https://www.python.org/downloads/"
    echo "         or install Homebrew from https://brew.sh and run: brew install python"
    echo
    echo "  Linux: Debian/Ubuntu: sudo apt install python3 python3-venv"
    echo "         Fedora:        sudo dnf install python3"
    echo
    printf "Press Enter to close..."
    read -r _
    exit 1
fi

"$PYTHON_CMD" scripts/launcher.py "$@"
EXITCODE=$?

echo
if [ "$EXITCODE" -ne 0 ]; then
    echo "  EveryTools stopped with an error. See the messages above."
else
    echo "  EveryTools stopped."
fi
echo
printf "Press Enter to close..."
read -r _
exit "$EXITCODE"
