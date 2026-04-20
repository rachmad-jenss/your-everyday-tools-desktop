#!/usr/bin/env bash
# Launcher for Linux. Run with: ./run.sh
# (macOS users: use run.command — identical content, different filename
#  so Finder recognises it as double-clickable.)

exec "$(dirname "$0")/run.command" "$@"
