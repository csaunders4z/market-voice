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

if (Test-RealApiKeys ".env") {
    Write-Host "DUMMY values detected as real keys"
} else {
    Write-Host "DUMMY values NOT detected as real keys"
}
