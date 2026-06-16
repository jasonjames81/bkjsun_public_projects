@echo off
REM Job App LLM Helper - Windows launcher.
REM Double-click this file. First run sets things up (~1 minute), then opens the app.

cd /d "%~dp0"

echo ============================================
echo   Job App LLM Helper
echo ============================================
echo.

REM --- Python 3 required ---
where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed.
  echo Install it from https://www.python.org/downloads/
  echo IMPORTANT: on the first installer screen, check "Add python.exe to PATH".
  echo Then double-click this file again.
  echo.
  pause
  exit /b 1
)

REM --- First-run setup ---
REM Use the venv's python EXPLICITLY everywhere, so pip and the app share one
REM interpreter (relying on activate + ambient `python` drops deps in the wrong place).
set "VENV_PY=venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
  echo First-time setup ^(creating a local environment, ~1 minute^)...
  if exist venv rmdir /s /q venv
  python -m venv venv
  if errorlevel 1 (
    echo Could not create the environment.
    pause
    exit /b 1
  )
)

"%VENV_PY%" -m pip install --upgrade pip >nul 2>nul
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Could not install dependencies.
  pause
  exit /b 1
)

REM --- Optional: install Claude Code (use a Claude subscription, no API key) ---
where claude >nul 2>nul
if errorlevel 1 (
  where npm >nul 2>nul
  if not errorlevel 1 (
    echo.
    echo Optional: install Claude Code, so you can sign in with a Claude Pro/Max
    echo subscription instead of an API key. You can also skip this and paste an
    echo API key in the app, or set it up later from the app's AI provider panel.
    set /p ans="Install Claude Code now with npm? [y/N] "
    if /i "%ans%"=="y" (
      call npm install -g @anthropic-ai/claude-code || echo Install failed - you can still use an API key in the app.
    )
  )
)

REM app.py opens the browser itself once it's up (set JALLM_NO_BROWSER=1 to skip).
echo.
echo Opening http://localhost:5000 in your browser.
echo First time in the app: open "AI provider", pick one, and paste an API key
echo (or use a Claude/ChatGPT/Gemini subscription via its CLI - see README).
echo.
echo Keep THIS window open while using the app. Close it to stop.
echo.
"%VENV_PY%" app.py
