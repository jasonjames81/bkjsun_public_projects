#!/usr/bin/env bash
# Start the Cover Letter AI Helper. Creates a venv on first run.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d venv ]; then
  echo "Creating virtual environment..."
  python -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install -q -r requirements.txt

# pandoc/pdftotext are optional (only used if you later add file parsing); not required.
echo "Open http://localhost:5000 in your browser"
python app.py
