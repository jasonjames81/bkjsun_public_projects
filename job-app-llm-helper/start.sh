#!/usr/bin/env bash
# Start the Job App LLM Helper. Creates a venv on first run.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d venv ]; then
  echo "Creating virtual environment..."
  python -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install -q -r requirements.txt

# File parsing (.pdf/.docx) is pure-Python via requirements.txt — no system binaries.
# app.py opens the browser itself once it's up (set JALLM_NO_BROWSER=1 to skip).
echo "Open http://localhost:5000 in your browser"
python app.py
