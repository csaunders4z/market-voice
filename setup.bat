@echo off
echo ========================================
echo MARKET VOICES - SETUP SCRIPT
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.8 or higher:
    echo 1. Download from https://www.python.org/downloads/
    echo 2. During installation, check "Add Python to PATH"
    echo 3. Restart this script after installation
    echo.
    pause
    exit /b 1
)

echo Python found! Installing dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
echo.
echo Next steps:
echo 1. Copy config.env.example to .env
echo 2. Add your API keys to .env file
echo 3. Run: python test_system.py
echo 4. Run: python main.py --test
echo.
pause 