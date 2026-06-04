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
if not exist venv (
  echo First-time setup ^(creating a local environment, ~1 minute^)...
  python -m venv venv
  if errorlevel 1 (
    echo Could not create the environment.
    pause
    exit /b 1
  )
)

call venv\Scripts\activate.bat
python -m pip install -q --upgrade pip >nul 2>nul
python -m pip install -q -r requirements.txt
if errorlevel 1 (
  echo Could not install dependencies.
  pause
  exit /b 1
)

REM Open the browser a moment after the server starts.
start "" /b cmd /c "timeout /t 2 >nul & start """" http://localhost:5000"

echo.
echo Opening http://localhost:5000 in your browser.
echo First time in the app: open "AI provider", pick one, and paste an API key
echo (or use a Claude/ChatGPT/Gemini subscription via its CLI - see README).
echo.
echo Keep THIS window open while using the app. Close it to stop.
echo.
python app.py
