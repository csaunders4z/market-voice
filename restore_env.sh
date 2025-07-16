#!/bin/bash


BACKUP_DIR="backups"
BACKUP_FILE=""
LIST_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --backup-file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        --list-only)
            LIST_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--backup-dir DIR] [--backup-file FILE] [--list-only]"
            echo "  --backup-dir DIR    Directory containing backup files (default: backups)"
            echo "  --backup-file FILE  Specific backup file to restore"
            echo "  --list-only         Only list available backups"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🔄 Environment File Restore Utility"
echo "===================================="

has_real_api_keys() {
    local env_file="$1"
    
    if [[ ! -f "$env_file" ]]; then
        return 1
    fi
    
    if grep -q "your_.*_api_key_here\|your_.*_key_here\|INSERT_.*_HERE\|REPLACE_.*_HERE" "$env_file"; then
        return 1
    fi
    
    local has_keys=false
    while IFS='=' read -r key value; do
        [[ "$key" =~ ^[[:space:]]*# ]] && continue
        [[ -z "$key" ]] && continue
        
        if [[ "$key" =~ API_KEY$ ]] && [[ -n "$value" ]] && [[ "$value" != "your_"*"_here" ]]; then
            has_keys=true
            break
        fi
    done < "$env_file"
    
    if $has_keys; then
        return 0
    else
        return 1
    fi
}

if [[ ! -d "$BACKUP_DIR" ]]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo -e "\nAvailable backups:"
backups=($(ls -t "$BACKUP_DIR"/.env.backup.* 2>/dev/null))

if [[ ${#backups[@]} -eq 0 ]]; then
    echo "❌ No backup files found in $BACKUP_DIR"
    exit 1
fi

for i in "${!backups[@]}"; do
    backup="${backups[$i]}"
    backup_name=$(basename "$backup")
    backup_date=$(stat -c %y "$backup" 2>/dev/null || stat -f %Sm "$backup" 2>/dev/null)
    
    if has_real_api_keys "$backup"; then
        key_status="✅ Has API keys"
    else
        key_status="⚠️  Template only"
    fi
    
    echo "  [$((i+1))] $backup_name - $backup_date - $key_status"
done

if $LIST_ONLY; then
    exit 0
fi

if [[ -n "$BACKUP_FILE" ]]; then
    selected_backup="$BACKUP_DIR/$BACKUP_FILE"
    if [[ ! -f "$selected_backup" ]]; then
        echo "❌ Specified backup file not found: $selected_backup"
        exit 1
    fi
else
    echo
    read -p "Select backup to restore (1-${#backups[@]}) or 'q' to quit: " selection
    
    if [[ "$selection" == "q" ]]; then
        echo "Operation cancelled"
        exit 0
    fi
    
    if ! [[ "$selection" =~ ^[0-9]+$ ]] || [[ "$selection" -lt 1 ]] || [[ "$selection" -gt ${#backups[@]} ]]; then
        echo "❌ Invalid selection"
        exit 1
    fi
    
    selected_backup="${backups[$((selection-1))]}"
fi

if ! has_real_api_keys "$selected_backup"; then
    echo "⚠️  Warning: Selected backup appears to contain template content, not real API keys"
    read -p "Continue anyway? (y/n): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Operation cancelled"
        exit 0
    fi
fi

if [[ -f ".env" ]]; then
    if has_real_api_keys ".env"; then
        echo "⚠️  Current .env file already contains real API keys"
        read -p "Overwrite current .env file? (y/n): " confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            echo "Operation cancelled"
            exit 0
        fi
    fi
fi

if cp "$selected_backup" ".env"; then
    echo "✅ Successfully restored .env from backup"
    echo "   Source: $selected_backup"
    echo "   Target: .env"
    
    if has_real_api_keys ".env"; then
        echo "✅ Verified: Restored .env contains real API keys"
    else
        echo "⚠️  Warning: Restored .env appears to contain template content"
    fi
else
    echo "❌ Failed to restore backup"
    exit 1
fi

echo -e "\n💡 Next steps:"
echo "   1. Verify your API keys are correct in .env"
echo "   2. Test your application to ensure it works"
echo "   3. Consider creating a fresh backup of your working .env"
