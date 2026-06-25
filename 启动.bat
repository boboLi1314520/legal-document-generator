@echo off
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    echo          https://www.python.org/downloads/
    pause
    exit /b 1
)

python launcher.py
pause
