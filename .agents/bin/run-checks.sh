#!/usr/bin/env bash
# Wrapper Bash para run-checks
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/run_checks.py" "$@"
