# Safe Environment Setup Script
# This script helps you set up your .env file safely

Write-Host "🔐 Market Voices Environment Setup" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Function to check if .env contains real API keys
function Test-RealApiKeys {
    param([string]$EnvFile)
    
    if (!(Test-Path $EnvFile)) {
        return $false
    }
    
    $content = Get-Content $EnvFile -Raw
    
    # Check for template placeholders
    if ($content -match "your_.*_api_key_here|your_.*_key_here|INSERT_.*_HERE|REPLACE_.*_HERE") {
        return $false
    }
    
    # Check for DUMMY/test values
    $lines = Get-Content $EnvFile
    $realKeyFound = $false
    $hasApiKeys = $false
    
    foreach ($line in $lines) {
        if ($line -match "^\s*#" -or $line -match "^\s*$") {
            continue  # Skip comments and empty lines
        }
        
        if ($line -match "^([^=]+)=(.+)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            
            if ($key -match "API_KEY$" -and $value) {
                $hasApiKeys = $true
                # Check if this is a real key (not DUMMY/TEST/PLACEHOLDER)
                if ($value -notmatch "^(DUMMY|TEST|PLACEHOLDER)\s*$" -and $value -notmatch "^your_.*_here$") {
                    $realKeyFound = $true
                    break
                }
            }
        }
    }
    
    return $realKeyFound
}

# Check if .env already exists
if (Test-Path ".env") {
    Write-Host "✅ .env file already exists - preserving existing configuration" -ForegroundColor Green
    Write-Host "   If you need to reset your .env file, please:" -ForegroundColor Yellow
    Write-Host "   1. Run backup_env.ps1 to create a backup" -ForegroundColor Yellow
    Write-Host "   2. Manually delete .env file" -ForegroundColor Yellow
    Write-Host "   3. Run this script again to create from template" -ForegroundColor Yellow
    exit 0
}

# Create .env from template only if it doesn't exist
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