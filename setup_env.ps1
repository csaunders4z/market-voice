# Safe Environment Setup Script
# This script helps you set up your .env file safely

Write-Host "🔐 Market Voices Environment Setup" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Check if .env already exists
if (Test-Path ".env") {
    Write-Host "⚠️  .env file already exists!" -ForegroundColor Yellow
    $backup = Read-Host "Do you want to create a backup first? (y/n)"
    if ($backup -eq "y" -or $backup -eq "Y") {
        & ".\backup_env.ps1"
    }
}

# Create .env from template
if (Test-Path "env.template") {
    Copy-Item "env.template" ".env"
    Write-Host "✅ Created .env from template" -ForegroundColor Green
} else {
    Write-Host "❌ env.template not found" -ForegroundColor Red
    exit 1
}

Write-Host "`n📝 Please edit .env and add your API keys:" -ForegroundColor Cyan
Write-Host "   - Alpha Vantage: https://www.alphavantage.co/support/#api-key" -ForegroundColor White
Write-Host "   - News API: https://newsapi.org/account" -ForegroundColor White
Write-Host "   - OpenAI: https://platform.openai.com/api-keys" -ForegroundColor White
Write-Host "   - RapidAPI: https://rapidapi.com/hub" -ForegroundColor White

Write-Host "`n💡 Remember:" -ForegroundColor Yellow
Write-Host "   - Never commit .env files to version control" -ForegroundColor Yellow
Write-Host "   - Run backup_env.ps1 before making changes" -ForegroundColor Yellow
Write-Host "   - Keep your API keys secure" -ForegroundColor Yellow

# Open .env file in default editor
$openFile = Read-Host "`nOpen .env file in editor now? (y/n)"
if ($openFile -eq "y" -or $openFile -eq "Y") {
    Start-Process ".env"
} 