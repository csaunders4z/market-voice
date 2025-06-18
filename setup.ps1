Write-Host "========================================" -ForegroundColor Green
Write-Host "MARKET VOICES - SETUP SCRIPT" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3.8 or higher:" -ForegroundColor Yellow
    Write-Host "1. Download from https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "2. During installation, check 'Add Python to PATH'" -ForegroundColor White
    Write-Host "3. Restart this script after installation" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Installing dependencies..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "Failed to install dependencies." -ForegroundColor Red
    Write-Host "Please check your internet connection and try again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "1. Copy config.env.example to .env" -ForegroundColor White
Write-Host "2. Add your API keys to .env file" -ForegroundColor White
Write-Host "3. Run: python test_system.py" -ForegroundColor White
Write-Host "4. Run: python main.py --test" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to continue" 