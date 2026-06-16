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

# --- Self-update ------------------------------------------------------------
# Pull the latest release in place (and clear the macOS quarantine flag) so you
# never have to re-download or re-approve in System Settings. Runs once per
# launch; set JALLM_NO_UPDATE=1 to skip. After a successful update we re-exec so
# the (possibly updated) launcher runs.
if [ -z "${JALLM_UPDATED:-}" ] && [ -f selfupdate.py ]; then
  export JALLM_UPDATED=1
  if python3 selfupdate.py; then exec "$0" "$@"; fi
fi

# --- First-run setup --------------------------------------------------------
# Use the venv's python EXPLICITLY everywhere. Relying on `source activate` +
# ambient `python3` is the classic cause of "deps installed but app can't import
# them": pip targets one interpreter, the app runs under another.
VENV_PY="venv/bin/python"
if [ ! -x "$VENV_PY" ]; then
  echo "First-time setup (creating a local environment, ~1 minute)…"
  rm -rf venv
  python3 -m venv venv || { echo "Could not create the environment."; read -r -p "Press Return to close."; exit 1; }
fi

"$VENV_PY" -m pip install --upgrade pip >/dev/null 2>&1
if ! "$VENV_PY" -m pip install -r requirements.txt; then
  echo
  echo "Dependency install failed (see above). Rebuilding the environment and retrying…"
  rm -rf venv
  python3 -m venv venv \
    && "$VENV_PY" -m pip install --upgrade pip >/dev/null 2>&1 \
    && "$VENV_PY" -m pip install -r requirements.txt \
    || { echo "Could not install dependencies."; read -r -p "Press Return to close."; exit 1; }
fi

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
"$VENV_PY" app.py
