#!/usr/bin/env bash
# Wrapper Bash para install.py
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if python --version >/dev/null 2>&1; then
    python "$SCRIPT_DIR/install.py" "$@"
elif python3 --version >/dev/null 2>&1; then
    python3 "$SCRIPT_DIR/install.py" "$@"
else
    py "$SCRIPT_DIR/install.py" "$@"
fi
