#!/bin/bash
# Job App LLM Helper — macOS launcher.
#
# HOW TO USE:
#   1. Double-click this file in Finder.
#   2. First time only: macOS blocks downloaded files.
#      - macOS 14 and earlier: right-click (Control-click) the file → Open → Open.
#      - macOS 15 Sequoia+ (only "Move to Trash"/"Cancel" shown): open
#        System Settings → Privacy & Security, click "Open Anyway", then launch again.
#      - Bulletproof: in Terminal run  xattr -cr  <this folder>  (drag the folder in).
#      You only do this once; after that, double-click works.
#
# It sets up everything on first run (about a minute), then opens the app in
# your browser. Keep the Terminal window open while you use it.

cd "$(dirname "$0")" || exit 1

echo "============================================"
echo "  Job App LLM Helper"
echo "============================================"
echo

# --- Python 3 required ------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed."
  echo
  echo "Install it, then double-click this file again:"
  echo "  • Easiest: download from https://www.python.org/downloads/"
  echo "  • Or with Homebrew:  brew install python"
  echo
  read -r -p "Press Return to close this window."
  exit 1
fi

# --- First-run setup --------------------------------------------------------
if [ ! -d venv ]; then
  echo "First-time setup (creating a local environment, ~1 minute)…"
  python3 -m venv venv || { echo "Could not create the environment."; read -r -p "Press Return to close."; exit 1; }
fi

# shellcheck disable=SC1091
source venv/bin/activate
python3 -m pip install -q --upgrade pip >/dev/null 2>&1
python3 -m pip install -q -r requirements.txt || { echo "Could not install dependencies."; read -r -p "Press Return to close."; exit 1; }

# --- Optional: install Claude Code (use a Claude subscription, no API key) ---
if ! command -v claude >/dev/null 2>&1; then
  if command -v npm >/dev/null 2>&1; then
    echo
    echo "Optional: install Claude Code, so you can sign in with a Claude Pro/Max"
    echo "subscription instead of an API key. (You can also skip this and paste an"
    echo "API key in the app, or set it up later from the app's AI provider panel.)"
    printf "Install Claude Code now with npm? [y/N] "
    read -r ans
    case "$ans" in
      [yY]*) npm install -g @anthropic-ai/claude-code || echo "Install failed — you can still use an API key in the app." ;;
    esac
  fi
fi

# --- Launch -----------------------------------------------------------------
# app.py opens the browser itself once it's up (set JALLM_NO_BROWSER=1 to skip).
echo
echo "Opening http://localhost:5000 in your browser."
echo "First time in the app: open “AI provider”, pick one, and paste an API key."
echo
echo "Keep THIS window open while using the app. Close it (or press Ctrl+C) to stop."
echo
python3 app.py
