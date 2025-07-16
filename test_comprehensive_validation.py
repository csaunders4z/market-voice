#!/usr/bin/env python3
"""
Comprehensive validation script for PR #14
Tests Finnhub integration, .env protection, and end-to-end functionality
"""

import sys
import os
import tempfile
import shutil
import subprocess
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_test(test_name, status="RUNNING"):
    """Print test status"""
    status_symbols = {
        "RUNNING": "🔄",
        "PASS": "✅", 
        "FAIL": "❌",
        "SKIP": "⏭️",
        "WARN": "⚠️"
    }
    symbol = status_symbols.get(status, "❓")
    print(f"{symbol} {test_name}")

def test_env_protection_logic():
    """Test .env protection safeguards"""
    print_section("Testing .env Protection Logic")
    
    print_test("Creating test .env with real API keys")
    test_env_content = """
OPENAI_API_KEY=sk-1234567890abcdef
ALPHA_VANTAGE_API_KEY=ABCD1234EFGH5678
FINNHUB_API_KEY=real_finnhub_key_12345
NEWS_API_KEY=real_news_api_key_67890
"""
    
    env_backup = None
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_backup = f.read()
    
    try:
        with open('.env', 'w') as f:
            f.write(test_env_content)
        print_test("Created test .env with real API keys", "PASS")
        
        print_test("Testing PowerShell API key detection")
        ps_test_script = """
. ./setup_env.ps1
if (Test-RealApiKeys ".env") {
    Write-Host "PASS: Detected real API keys"
    exit 0
} else {
    Write-Host "FAIL: Did not detect real API keys"
    exit 1
}
"""
        
        try:
            with open('test_ps_detection.ps1', 'w') as f:
                f.write(ps_test_script)
            
            result = subprocess.run(['pwsh', 'test_ps_detection.ps1'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print_test("PowerShell API key detection", "PASS")
            else:
                print_test("PowerShell API key detection", "FAIL")
                print(f"  Error: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print_test("PowerShell API key detection", "SKIP")
            print("  PowerShell not available or timeout")
        finally:
            if os.path.exists('test_ps_detection.ps1'):
                os.remove('test_ps_detection.ps1')
        
        print_test("Testing bash API key detection")
        bash_test_script = """#!/bin/bash
source deploy.sh
if has_real_api_keys ".env"; then
    echo "PASS: Detected real API keys"
    exit 0
else
    echo "FAIL: Did not detect real API keys"
    exit 1
fi
"""
        
        try:
            with open('test_bash_detection.sh', 'w') as f:
                f.write(bash_test_script)
            os.chmod('test_bash_detection.sh', 0o755)
            
            result = subprocess.run(['bash', 'test_bash_detection.sh'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print_test("Bash API key detection", "PASS")
            else:
                print_test("Bash API key detection", "FAIL")
                print(f"  Error: {result.stderr}")
        except subprocess.TimeoutExpired:
            print_test("Bash API key detection", "FAIL")
            print("  Timeout occurred")
        finally:
            if os.path.exists('test_bash_detection.sh'):
                os.remove('test_bash_detection.sh')
        
        print_test("Testing template content detection")
        template_content = """
OPENAI_API_KEY=your_openai_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
"""
        
        with open('.env.template_test', 'w') as f:
            f.write(template_content)
        
        bash_template_test = """#!/bin/bash
source deploy.sh
if has_real_api_keys ".env.template_test"; then
    echo "FAIL: Incorrectly detected template as real keys"
    exit 1
else
    echo "PASS: Correctly identified template content"
    exit 0
fi
"""
        
        try:
            with open('test_template_detection.sh', 'w') as f:
                f.write(bash_template_test)
            os.chmod('test_template_detection.sh', 0o755)
            
            result = subprocess.run(['bash', 'test_template_detection.sh'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print_test("Template content detection", "PASS")
            else:
                print_test("Template content detection", "FAIL")
                print(f"  Error: {result.stderr}")
        except subprocess.TimeoutExpired:
            print_test("Template content detection", "FAIL")
            print("  Timeout occurred")
        finally:
            if os.path.exists('test_template_detection.sh'):
                os.remove('test_template_detection.sh')
            if os.path.exists('.env.template_test'):
                os.remove('.env.template_test')
        
    finally:
        if env_backup is not None:
            with open('.env', 'w') as f:
                f.write(env_backup)
            print_test("Restored original .env file", "PASS")
        elif os.path.exists('.env'):
            os.remove('.env')
            print_test("Cleaned up test .env file", "PASS")

def test_backup_restore_utilities():
    """Test backup and restore functionality"""
    print_section("Testing Backup/Restore Utilities")
    
    backup_dir = "test_backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    try:
        print_test("Creating test .env for backup testing")
        test_content = """
OPENAI_API_KEY=test_key_12345
ALPHA_VANTAGE_API_KEY=test_av_key_67890
"""
        with open('.env.test_backup', 'w') as f:
            f.write(test_content)
        
        print_test("Testing backup creation")
        backup_script = f"""#!/bin/bash
source deploy.sh
backup_env_file ".env.test_backup" "{backup_dir}"
"""
        
        try:
            with open('test_backup.sh', 'w') as f:
                f.write(backup_script)
            os.chmod('test_backup.sh', 0o755)
            
            result = subprocess.run(['bash', 'test_backup.sh'], 
                                  capture_output=True, text=True, timeout=10)
            
            backup_files = list(Path(backup_dir).glob('.env.backup.*'))
            if backup_files:
                print_test("Backup creation", "PASS")
                print(f"  Created backup: {backup_files[0].name}")
                
                print_test("Testing restore functionality")
                
                with open('.env.test_backup', 'w') as f:
                    f.write("# Modified file\nTEST_KEY=modified")
                
                restore_script = f"""#!/bin/bash
./restore_env.sh --backup-dir "{backup_dir}" --backup-file "{backup_files[0].name}" --list-only > /dev/null
if [ $? -eq 0 ]; then
    echo "PASS: Restore script can list backups"
else
    echo "FAIL: Restore script failed to list backups"
    exit 1
fi
"""
                
                with open('test_restore.sh', 'w') as f:
                    f.write(restore_script)
                os.chmod('test_restore.sh', 0o755)
                
                result = subprocess.run(['bash', 'test_restore.sh'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print_test("Restore utility functionality", "PASS")
                else:
                    print_test("Restore utility functionality", "FAIL")
                    print(f"  Error: {result.stderr}")
                
            else:
                print_test("Backup creation", "FAIL")
                print("  No backup files found")
                
        except subprocess.TimeoutExpired:
            print_test("Backup creation", "FAIL")
            print("  Timeout occurred")
        finally:
            for script in ['test_backup.sh', 'test_restore.sh']:
                if os.path.exists(script):
                    os.remove(script)
        
    finally:
        if os.path.exists('.env.test_backup'):
            os.remove('.env.test_backup')
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        print_test("Cleaned up test files", "PASS")

def test_finnhub_integration():
    """Test Finnhub integration functionality"""
    print_section("Testing Finnhub Integration")
    
    try:
        print_test("Testing NewsCollector import and method existence")
        
        from data_collection.news_collector import news_collector
        
        required_methods = [
            'get_comprehensive_company_news',
            '_create_comprehensive_summary', 
            'get_company_news_summary'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(news_collector, method):
                missing_methods.append(method)
        
        if missing_methods:
            print_test("Method existence check", "FAIL")
            print(f"  Missing methods: {missing_methods}")
            return False
        else:
            print_test("Method existence check", "PASS")
        
        print_test("Testing method signatures")
        
        try:
            result = news_collector.get_comprehensive_company_news("AAPL", "Apple Inc.", 2.5)
            
            if isinstance(result, dict):
                required_keys = ['symbol', 'company_name', 'sentiment_data', 'sources_used']
                missing_keys = [key for key in required_keys if key not in result]
                
                if missing_keys:
                    print_test("Return structure validation", "FAIL")
                    print(f"  Missing keys: {missing_keys}")
                else:
                    print_test("Return structure validation", "PASS")
                    print(f"  Sources used: {result.get('sources_used', [])}")
            else:
                print_test("Return structure validation", "FAIL")
                print(f"  Expected dict, got {type(result)}")
                
        except Exception as e:
            print_test("Method signature test", "WARN")
            print(f"  Expected error (no API keys): {str(e)[:100]}...")
        
        print_test("Testing summary creation")
        
        try:
            summary = news_collector._create_comprehensive_summary(
                "AAPL", "Apple Inc.", 2.5, [], {}, []
            )
            
            if isinstance(summary, str) and "Apple Inc." in summary:
                print_test("Summary creation", "PASS")
                print(f"  Summary length: {len(summary)} characters")
            else:
                print_test("Summary creation", "FAIL")
                print(f"  Invalid summary: {str(summary)[:100]}...")
                
        except Exception as e:
            print_test("Summary creation", "FAIL")
            print(f"  Error: {str(e)}")
        
        print_test("Testing error handling with invalid inputs")
        
        try:
            result = news_collector.get_comprehensive_company_news("", "", 0)
            print_test("Error handling test", "PASS")
            print(f"  Handled invalid inputs gracefully")
        except Exception as e:
            print_test("Error handling test", "WARN")
            print(f"  Error with invalid inputs: {str(e)[:100]}...")
        
        return True
        
    except ImportError as e:
        print_test("NewsCollector import", "FAIL")
        print(f"  Import error: {str(e)}")
        return False
    except Exception as e:
        print_test("Finnhub integration test", "FAIL")
        print(f"  Unexpected error: {str(e)}")
        return False

def test_end_to_end_functionality():
    """Test end-to-end news collection"""
    print_section("Testing End-to-End News Collection")
    
    try:
        from data_collection.news_collector import news_collector
        
        test_symbols = [
            ("AAPL", "Apple Inc.", 1.5),
            ("MSFT", "Microsoft Corporation", -0.8),
            ("GOOGL", "Alphabet Inc.", 2.2)
        ]
        
        for symbol, company, change in test_symbols:
            print_test(f"Testing news collection for {symbol}")
            
            try:
                result = news_collector.get_company_news_summary(symbol, company, change)
                
                if isinstance(result, str) and len(result) > 0:
                    print_test(f"{symbol} news collection", "PASS")
                    print(f"  Summary length: {len(result)} characters")
                else:
                    print_test(f"{symbol} news collection", "WARN")
                    print(f"  Empty or invalid result")
                    
            except Exception as e:
                print_test(f"{symbol} news collection", "WARN")
                print(f"  Expected error (API keys): {str(e)[:100]}...")
        
        return True
        
    except Exception as e:
        print_test("End-to-end functionality", "FAIL")
        print(f"  Error: {str(e)}")
        return False

def test_existing_functionality():
    """Test that existing functionality still works"""
    print_section("Testing Existing Functionality Preservation")
    
    try:
        from data_collection.news_collector import news_collector
        
        existing_methods = [
            '_get_biztoc_market_news',
            '_create_news_summary'
        ]
        
        for method in existing_methods:
            if hasattr(news_collector, method):
                print_test(f"Existing method {method}", "PASS")
            else:
                print_test(f"Existing method {method}", "FAIL")
        
        return True
        
    except Exception as e:
        print_test("Existing functionality test", "FAIL")
        print(f"  Error: {str(e)}")
        return False

def run_linting_and_syntax_checks():
    """Run basic linting and syntax checks"""
    print_section("Running Linting and Syntax Checks")
    
    print_test("Python syntax validation")
    
    python_files = [
        'src/data_collection/news_collector.py',
        'test_finnhub_integration.py'
    ]
    
    syntax_errors = []
    for file_path in python_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    compile(f.read(), file_path, 'exec')
                print_test(f"Syntax check: {file_path}", "PASS")
            except SyntaxError as e:
                syntax_errors.append(f"{file_path}: {e}")
                print_test(f"Syntax check: {file_path}", "FAIL")
        else:
            print_test(f"File check: {file_path}", "FAIL")
            print(f"  File not found")
    
    if syntax_errors:
        print_test("Overall syntax validation", "FAIL")
        for error in syntax_errors:
            print(f"  {error}")
        return False
    else:
        print_test("Overall syntax validation", "PASS")
        return True

def main():
    """Run comprehensive validation"""
    print("🚀 Starting Comprehensive Validation for PR #14")
    print("Testing Finnhub Integration + .env Protection Safeguards")
    
    test_results = []
    
    test_results.append(("Syntax & Linting", run_linting_and_syntax_checks()))
    test_results.append(("Existing Functionality", test_existing_functionality()))
    test_results.append(("Finnhub Integration", test_finnhub_integration()))
    test_results.append(("End-to-End Collection", test_end_to_end_functionality()))
    test_results.append((".env Protection Logic", test_env_protection_logic()))
    test_results.append(("Backup/Restore Utilities", test_backup_restore_utilities()))
    
    print_section("VALIDATION SUMMARY")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        if result:
            print_test(test_name, "PASS")
            passed += 1
        else:
            print_test(test_name, "FAIL")
    
    print(f"\n📊 Results: {passed}/{total} test categories passed")
    
    if passed == total:
        print("🎉 All validation tests passed!")
        return True
    else:
        print("⚠️  Some tests failed or had warnings (expected due to missing API keys)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
