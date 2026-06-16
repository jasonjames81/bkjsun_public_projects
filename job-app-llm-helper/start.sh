#!/usr/bin/env bash
# Start the Job App LLM Helper. Creates a venv on first run.
set -euo pipefail
cd "$(dirname "$0")"

# Self-update in place from the latest release, then re-exec. Set JALLM_NO_UPDATE=1
# to skip (offline / pinned). Runs once per launch via the JALLM_UPDATED guard.
if [ -z "${JALLM_UPDATED:-}" ] && [ -f selfupdate.py ] && command -v python3 >/dev/null 2>&1; then
  export JALLM_UPDATED=1
  if python3 selfupdate.py; then exec "$0" "$@"; fi
fi

# Use the venv's python explicitly so pip and the app share one interpreter.
VENV_PY="venv/bin/python"
if [ ! -x "$VENV_PY" ]; then
  echo "Creating virtual environment..."
  rm -rf venv
  python3 -m venv venv
fi
"$VENV_PY" -m pip install -q -r requirements.txt

# File parsing (.pdf/.docx) is pure-Python via requirements.txt — no system binaries.
# app.py opens the browser itself once it's up (set JALLM_NO_BROWSER=1 to skip).
echo "Open http://localhost:5000 in your browser"
"$VENV_PY" app.py
