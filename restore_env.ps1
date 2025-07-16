# Restore Environment File Script
# This script helps restore API keys from backup files

param(
    [string]$BackupDir = "backups",
    [string]$BackupFile = "",
    [switch]$ListOnly
)

Write-Host "🔄 Environment File Restore Utility" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

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
            continue
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

# Check if backup directory exists
if (!(Test-Path $BackupDir)) {
    Write-Host "❌ Backup directory not found: $BackupDir" -ForegroundColor Red
    exit 1
}

# List available backups
$backups = Get-ChildItem "$BackupDir\.env.backup.*" | Sort-Object LastWriteTime -Descending

if ($backups.Count -eq 0) {
    Write-Host "❌ No backup files found in $BackupDir" -ForegroundColor Red
    exit 1
}

Write-Host "`nAvailable backups:" -ForegroundColor Cyan
for ($i = 0; $i -lt $backups.Count; $i++) {
    $backup = $backups[$i]
    $hasKeys = Test-RealApiKeys $backup.FullName
    $keyStatus = if ($hasKeys) { "✅ Has API keys" } else { "⚠️  Template only" }
    Write-Host "  [$($i+1)] $($backup.Name) - $($backup.LastWriteTime) - $keyStatus"
}

if ($ListOnly) {
    exit 0
}

# Select backup to restore
if ($BackupFile) {
    $selectedBackup = Join-Path $BackupDir $BackupFile
    if (!(Test-Path $selectedBackup)) {
        Write-Host "❌ Specified backup file not found: $selectedBackup" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host ""
    $selection = Read-Host "Select backup to restore (1-$($backups.Count)) or 'q' to quit"
    
    if ($selection -eq 'q') {
        Write-Host "Operation cancelled" -ForegroundColor Yellow
        exit 0
    }
    
    $index = [int]$selection - 1
    if ($index -lt 0 -or $index -ge $backups.Count) {
        Write-Host "❌ Invalid selection" -ForegroundColor Red
        exit 1
    }
    
    $selectedBackup = $backups[$index].FullName
}

# Verify the backup has real API keys
if (!(Test-RealApiKeys $selectedBackup)) {
    Write-Host "⚠️  Warning: Selected backup appears to contain template content, not real API keys" -ForegroundColor Yellow
    $confirm = Read-Host "Continue anyway? (y/n)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "Operation cancelled" -ForegroundColor Yellow
        exit 0
    }
}

# Check current .env status
if (Test-Path ".env") {
    if (Test-RealApiKeys ".env") {
        Write-Host "⚠️  Current .env file already contains real API keys" -ForegroundColor Yellow
        $confirm = Read-Host "Overwrite current .env file? (y/n)"
        if ($confirm -ne "y" -and $confirm -ne "Y") {
            Write-Host "Operation cancelled" -ForegroundColor Yellow
            exit 0
        }
    }
}

# Restore the backup
try {
    Copy-Item $selectedBackup ".env"
    Write-Host "✅ Successfully restored .env from backup" -ForegroundColor Green
    Write-Host "   Source: $selectedBackup" -ForegroundColor Gray
    Write-Host "   Target: .env" -ForegroundColor Gray
    
    # Verify restoration
    if (Test-RealApiKeys ".env") {
        Write-Host "✅ Verified: Restored .env contains real API keys" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Warning: Restored .env appears to contain template content" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Failed to restore backup: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n💡 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Verify your API keys are correct in .env" -ForegroundColor White
Write-Host "   2. Test your application to ensure it works" -ForegroundColor White
Write-Host "   3. Consider running backup_env.ps1 to create a fresh backup" -ForegroundColor White
