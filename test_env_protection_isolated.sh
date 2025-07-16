#!/bin/bash

echo "🔍 Testing .env Protection Logic (Isolated)"
echo "==========================================="

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

backup_env_file() {
    local env_file="$1"
    local backup_dir="$2"
    
    if [[ ! -f "$env_file" ]]; then
        return 0
    fi
    
    mkdir -p "$backup_dir"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/.env.backup.$timestamp"
    
    cp "$env_file" "$backup_file"
    echo "Created backup: $backup_file"
}

test_real_api_key_detection() {
    echo "Testing real API key detection..."
    
    cat > test_real.env << 'EOF'
ALPHA_VANTAGE_API_KEY=abc123def456
THE_NEWS_API_API_KEY=xyz789uvw012
OPENAI_API_KEY=sk-proj-abcdef123456
EOF
    
    if has_real_api_keys "test_real.env"; then
        echo "✅ Correctly detected real API keys"
    else
        echo "❌ Failed to detect real API keys"
    fi
    
    rm -f test_real.env
}

test_template_detection() {
    echo "Testing template content detection..."
    
    cat > test_template.env << 'EOF'
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
THE_NEWS_API_API_KEY=your_news_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
EOF
    
    if has_real_api_keys "test_template.env"; then
        echo "❌ Incorrectly detected template as real keys"
    else
        echo "✅ Correctly detected template content"
    fi
    
    rm -f test_template.env
}

test_dummy_detection() {
    echo "Testing DUMMY key detection..."
    
    cat > test_dummy.env << 'EOF'
ALPHA_VANTAGE_API_KEY=DUMMY
THE_NEWS_API_API_KEY=DUMMY
OPENAI_API_KEY=DUMMY
EOF
    
    if has_real_api_keys "test_dummy.env"; then
        echo "⚠️  DUMMY detected as real keys (may be expected behavior)"
    else
        echo "✅ Correctly detected DUMMY content"
    fi
    
    rm -f test_dummy.env
}

test_backup_functionality() {
    echo "Testing backup functionality..."
    
    cat > test_backup.env << 'EOF'
ALPHA_VANTAGE_API_KEY=real_key_123
THE_NEWS_API_API_KEY=real_key_456
EOF
    
    backup_env_file "test_backup.env" "test_backups"
    
    if [[ -d "test_backups" ]] && [[ "$(ls -A test_backups 2>/dev/null)" ]]; then
        echo "✅ Backup functionality works"
        rm -rf test_backups
    else
        echo "❌ Backup functionality failed"
    fi
    
    rm -f test_backup.env
}

test_nonexistent_file() {
    echo "Testing nonexistent file handling..."
    
    if has_real_api_keys "nonexistent.env"; then
        echo "❌ Incorrectly detected keys in nonexistent file"
    else
        echo "✅ Correctly handled nonexistent file"
    fi
}

echo "Running .env protection tests..."
test_real_api_key_detection
test_template_detection
test_dummy_detection
test_backup_functionality
test_nonexistent_file

echo ""
echo "✅ .env protection logic tests completed"
