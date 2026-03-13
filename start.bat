@echo off
chcp 65001 >nul
echo ========================================
echo Trading Tools
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo Starting Trading Tools on http://localhost:8505
echo Press Ctrl+C to stop
echo.

pythonw -m uvicorn app:app --host 0.0.0.0 --port 8505 --reload

pause
