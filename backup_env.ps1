# Backup Environment File Script
# This script creates a timestamped backup of your .env file

param(
    [string]$BackupDir = "backups"
)

# Create backup directory if it doesn't exist
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir
    Write-Host "Created backup directory: $BackupDir"
}

# Generate timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "$BackupDir\.env.backup.$timestamp"

# Check if .env exists
if (Test-Path ".env") {
    # Create backup
    Copy-Item ".env" $backupFile
    Write-Host "✅ Backup created: $backupFile"
    
    # Show recent backups
    Write-Host "`nRecent backups:"
    Get-ChildItem "$BackupDir\.env.backup.*" | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | ForEach-Object {
        Write-Host "  $($_.Name) - $($_.LastWriteTime)"
    }
} else {
    Write-Host "❌ No .env file found to backup"
}

Write-Host "`n💡 Tip: Run this script before making changes to .env" 