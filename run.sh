#!/usr/bin/env bash
# Launcher for Linux. Run with: ./run.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/run.command" "$@"
