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
    
    # Check for actual API key values
    $lines = Get-Content $EnvFile
    foreach ($line in $lines) {
        if ($line -match "^\s*#" -or $line -match "^\s*$") {
            continue  # Skip comments and empty lines
        }
        
        if ($line -match "^([^=]+)=(.+)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            
            if ($key -match "API_KEY$" -and $value -and $value -notmatch "^your_.*_here$") {
                return $true
            }
        }
    }
    
    return $false
}

# Check if .env already exists
if (Test-Path ".env") {
    if (Test-RealApiKeys ".env") {
        Write-Host "🚨 CRITICAL: .env file contains real API keys!" -ForegroundColor Red
        Write-Host "This operation will overwrite your existing API keys." -ForegroundColor Red
        Write-Host ""
        
        $backup = Read-Host "Create backup before proceeding? (STRONGLY RECOMMENDED) (y/n)"
        if ($backup -eq "y" -or $backup -eq "Y") {
            & ".\backup_env.ps1"
            Write-Host "✅ Backup created" -ForegroundColor Green
        } else {
            Write-Host "⚠️  No backup created - your API keys will be lost!" -ForegroundColor Yellow
        }
        
        Write-Host ""
        $confirm = Read-Host "Are you SURE you want to overwrite .env with template? (yes/no)"
        if ($confirm -ne "yes") {
            Write-Host "❌ Operation cancelled to protect your API keys" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "⚠️  .env file already exists (contains template content)" -ForegroundColor Yellow
        $backup = Read-Host "Do you want to create a backup first? (y/n)"
        if ($backup -eq "y" -or $backup -eq "Y") {
            & ".\backup_env.ps1"
        }
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