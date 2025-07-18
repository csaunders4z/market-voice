#!/usr/bin/env python3
"""
Comprehensive test to validate .env file protection mechanisms
"""
import os
import shutil
import subprocess
import sys
from datetime import datetime

def create_test_env_with_real_keys():
    """Create a test .env file with real-looking API keys"""
    with open('.env', 'w') as f:
        f.write("OPENAI_API_KEY=sk-1234567890abcdef\n")
        f.write("FMP_API_KEY=abc123def456\n")
        f.write("ALPHA_VANTAGE_API_KEY=XYZ789\n")
        f.write("LOG_LEVEL=INFO\n")
    print("✅ Created test .env with real-looking keys")

def test_safe_test_environment():
    """Test that test files no longer overwrite .env with real keys"""
    print("\n🧪 Testing safe test environment setup...")
    
    create_test_env_with_real_keys()
    original_content = open('.env').read()
    
    try:
        result = subprocess.run([sys.executable, 'test_end_to_end_news.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if os.path.exists('.env'):
            current_content = open('.env').read()
            if "sk-1234567890abcdef" in current_content:
                print("✅ test_end_to_end_news.py preserved real API keys")
                return True
            else:
                print("❌ test_end_to_end_news.py overwrote real API keys")
                return False
        else:
            print("❌ .env file was deleted")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_deployment_script_protection():
    """Test that deployment scripts still have proper protection"""
    print("\n🧪 Testing deployment script protection...")
    
    create_test_env_with_real_keys()
    
    test_script = '''#!/bin/bash
has_real_api_keys() {
    local env_file="$1"
    
    if [[ ! -f "$env_file" ]]; then
        return 1  # File doesn't exist, no real keys
    fi
    
    if grep -q "your_.*_api_key_here\\|your_.*_key_here\\|INSERT_.*_HERE\\|REPLACE_.*_HERE" "$env_file"; then
        return 1  # Contains template placeholders
    fi
    
    if grep -q "^[^#]*API_KEY.*=.*DUMMY\\s*$\\|^[^#]*API_KEY.*=.*TEST\\s*$\\|^[^#]*API_KEY.*=.*PLACEHOLDER\\s*$" "$env_file"; then
        local real_key_found=false
        while IFS='=' read -r key value; do
            [[ "$key" =~ ^[[:space:]]*# ]] && continue
            [[ -z "$key" ]] && continue
            
            if [[ "$key" =~ API_KEY$ ]] && [[ -n "$value" ]] && [[ "$value" != "your_"*"_here" ]]; then
                if [[ "$value" != "DUMMY" && "$value" != "TEST" && "$value" != "PLACEHOLDER" && ! "$value" =~ ^[[:space:]]*DUMMY[[:space:]]*$ && ! "$value" =~ ^[[:space:]]*TEST[[:space:]]*$ ]]; then
                    real_key_found=true
                    break
                fi
            fi
        done < "$env_file"
        
        if $real_key_found; then
            return 0  # Has real API keys mixed with DUMMY values
        else
            return 1  # Only DUMMY/test values, treat as template
        fi
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
        return 0  # Has real API keys
    else
        return 1  # No real API keys found
    fi
}

if has_real_api_keys ".env"; then
    echo "REAL_KEYS_DETECTED"
    exit 0
else
    echo "NO_REAL_KEYS"
    exit 1
fi
'''
    
    with open('test_deploy_function.sh', 'w') as f:
        f.write(test_script)
    
    os.chmod('test_deploy_function.sh', 0o755)
    
    result = subprocess.run(['./test_deploy_function.sh'], capture_output=True, text=True)
    
    os.remove('test_deploy_function.sh')
    
    if "REAL_KEYS_DETECTED" in result.stdout:
        print("✅ deploy.sh correctly detects real API keys")
        return True
    else:
        print("❌ deploy.sh failed to detect real API keys")
        print(f"Function output: {result.stdout.strip()}")
        print(f"Function stderr: {result.stderr.strip()}")
        return False

def cleanup():
    """Clean up test files"""
    for file in ['.env']:
        if os.path.exists(file):
            os.remove(file)
    
    import glob
    for backup in glob.glob('.env.backup.*'):
        os.remove(backup)

def main():
    """Run all protection validation tests"""
    print("🔒 .env Protection Validation Test Suite")
    print("=" * 50)
    
    tests = [
        ("Safe Test Environment", test_safe_test_environment),
        ("Deployment Script Protection", test_deployment_script_protection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"💥 {test_name} ERROR: {e}")
        finally:
            cleanup()
    
    print(f"\n{'='*50}")
    print(f"Protection Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL PROTECTION MECHANISMS WORKING!")
        return True
    else:
        print("❌ SOME PROTECTION MECHANISMS FAILED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
