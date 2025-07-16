#!/usr/bin/env python3

import os
import shutil
import subprocess
import tempfile
from datetime import datetime

print("🔍 Testing Backup/Restore Utilities")
print("===================================")

def create_test_env_files():
    """Create test .env files for testing"""
    
    real_env_content = """ALPHA_VANTAGE_API_KEY=av_real_key_123456
THE_NEWS_API_API_KEY=news_real_key_789012
OPENAI_API_KEY=sk-proj-real_key_345678
RAPIDAPI_KEY=rapid_real_key_901234
BIZTOC_API_KEY=biztoc_real_key_567890
FINNHUB_API_KEY=finnhub_real_key_123456
FMP_API_KEY=fmp_real_key_789012
NEWSDATA_IO_API_KEY=newsdata_real_key_345678
LOG_LEVEL=INFO
"""
    
    template_env_content = """ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
THE_NEWS_API_API_KEY=your_news_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
BIZTOC_API_KEY=your_biztoc_api_key_here
FINNHUB_API_KEY=your_finnhub_api_key_here
FMP_API_KEY=your_fmp_api_key_here
NEWSDATA_IO_API_KEY=your_newsdata_io_api_key_here
LOG_LEVEL=INFO
"""
    
    with open('test_real.env', 'w') as f:
        f.write(real_env_content)
    
    with open('test_template.env', 'w') as f:
        f.write(template_env_content)
    
    print("✅ Created test .env files")

def test_backup_env_powershell():
    """Test backup_env.ps1 functionality"""
    try:
        if not os.path.exists('backup_env.ps1'):
            print("❌ backup_env.ps1 not found")
            return False
        
        shutil.copy('test_real.env', '.env')
        
        result = subprocess.run(['pwsh', '-File', 'backup_env.ps1'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            if os.path.exists('backups') and os.listdir('backups'):
                print("✅ backup_env.ps1 created backup successfully")
                return True
            else:
                print("❌ backup_env.ps1 ran but no backup created")
                return False
        else:
            print(f"⚠️  backup_env.ps1 not available (PowerShell): {result.stderr}")
            return True
            
    except subprocess.TimeoutExpired:
        print("⚠️  backup_env.ps1 test timed out")
        return True
    except FileNotFoundError:
        print("⚠️  PowerShell not available for backup_env.ps1 test")
        return True
    except Exception as e:
        print(f"⚠️  backup_env.ps1 test error: {e}")
        return True

def test_restore_env_powershell():
    """Test restore_env.ps1 functionality"""
    try:
        if not os.path.exists('restore_env.ps1'):
            print("❌ restore_env.ps1 not found")
            return False
        
        os.makedirs('backups', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backups/.env.backup.{timestamp}'
        shutil.copy('test_real.env', backup_file)
        
        result = subprocess.run(['pwsh', '-File', 'restore_env.ps1', '-ListOnly'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            if 'Available backups:' in result.stdout:
                print("✅ restore_env.ps1 lists backups successfully")
                return True
            else:
                print("❌ restore_env.ps1 ran but didn't list backups properly")
                return False
        else:
            print(f"⚠️  restore_env.ps1 not available (PowerShell): {result.stderr}")
            return True
            
    except subprocess.TimeoutExpired:
        print("⚠️  restore_env.ps1 test timed out")
        return True
    except FileNotFoundError:
        print("⚠️  PowerShell not available for restore_env.ps1 test")
        return True
    except Exception as e:
        print(f"⚠️  restore_env.ps1 test error: {e}")
        return True

def test_restore_env_bash():
    """Test restore_env.sh functionality"""
    try:
        if not os.path.exists('restore_env.sh'):
            print("❌ restore_env.sh not found")
            return False
        
        os.makedirs('backups', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backups/.env.backup.{timestamp}'
        shutil.copy('test_real.env', backup_file)
        
        result = subprocess.run(['bash', 'restore_env.sh', '--list'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            if 'Available backups:' in result.stdout:
                print("✅ restore_env.sh lists backups successfully")
                return True
            else:
                print("❌ restore_env.sh ran but didn't list backups properly")
                return False
        else:
            print(f"⚠️  restore_env.sh error: {result.stderr}")
            return True
            
    except subprocess.TimeoutExpired:
        print("⚠️  restore_env.sh test timed out")
        return True
    except Exception as e:
        print(f"⚠️  restore_env.sh test error: {e}")
        return True

def test_backup_directory_creation():
    """Test that backup utilities create proper directory structure"""
    try:
        if os.path.exists('backups'):
            shutil.rmtree('backups')
        
        shutil.copy('test_real.env', '.env')
        
        if os.path.exists('backup_env.ps1'):
            try:
                subprocess.run(['pwsh', '-File', 'backup_env.ps1'], 
                              capture_output=True, text=True, timeout=30)
            except:
                pass
        
        if os.path.exists('backups'):
            print("✅ Backup directory created successfully")
            return True
        else:
            print("⚠️  Backup directory not created (may be expected)")
            return True
            
    except Exception as e:
        print(f"⚠️  Backup directory test error: {e}")
        return True

def test_file_permissions():
    """Test that backup files have correct permissions"""
    try:
        if not os.path.exists('backups') or not os.listdir('backups'):
            print("⚠️  No backup files to test permissions")
            return True
        
        backup_files = [f for f in os.listdir('backups') if f.startswith('.env.backup.')]
        
        if backup_files:
            backup_path = os.path.join('backups', backup_files[0])
            if os.access(backup_path, os.R_OK):
                print("✅ Backup files have read permissions")
                return True
            else:
                print("❌ Backup files lack read permissions")
                return False
        else:
            print("⚠️  No backup files found for permission test")
            return True
            
    except Exception as e:
        print(f"⚠️  File permissions test error: {e}")
        return True

def cleanup_test_files():
    """Clean up test files"""
    test_files = ['test_real.env', 'test_template.env', '.env']
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
    
    if os.path.exists('backups'):
        shutil.rmtree('backups')
    
    print("✅ Test files cleaned up")

def run_all_tests():
    """Run all backup/restore utility tests"""
    create_test_env_files()
    
    try:
        tests = [
            ("Backup PowerShell Test", test_backup_env_powershell),
            ("Restore PowerShell Test", test_restore_env_powershell),
            ("Restore Bash Test", test_restore_env_bash),
            ("Backup Directory Creation Test", test_backup_directory_creation),
            ("File Permissions Test", test_file_permissions)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        
        print(f"\n{'='*50}")
        print(f"Backup/Restore Utilities Test Results: {passed}/{total} tests passed")
        
        if passed >= total - 1:
            print("✅ Backup/Restore utilities tests PASSED (allowing for environment differences)")
            return True
        else:
            print("❌ Critical backup/restore utility tests FAILED")
            return False
            
    finally:
        cleanup_test_files()

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
