import os
import shutil
import tempfile
from pathlib import Path
from contextlib import contextmanager

class SafeTestEnvironment:
    """Safely manage test environments without overwriting real .env files"""
    
    @staticmethod
    def has_real_api_keys(env_file):
        """Check if .env file contains real API keys (not template placeholders or DUMMY values)"""
        if not Path(env_file).exists():
            return False
        
        with open(env_file, 'r') as f:
            content = f.read()
        
        if any(placeholder in content for placeholder in [
            "your_", "_api_key_here", "_key_here", "INSERT_", "REPLACE_"
        ]):
            return False
        
        lines = content.split('\n')
        real_key_found = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('#') or not line or '=' not in line:
                continue
                
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            if key.endswith('API_KEY') and value:
                if value not in ['DUMMY', 'TEST', 'PLACEHOLDER'] and not value.startswith('your_'):
                    real_key_found = True
                    break
        
        return real_key_found
    
    @contextmanager
    def safe_test_env(self, test_env_file='test_env_dummy.env'):
        """Context manager for safe test environment setup"""
        original_env_backup = None
        
        try:
            if os.path.exists('.env') and self.has_real_api_keys('.env'):
                original_env_backup = '.env.test_backup_' + str(os.getpid())
                shutil.copy('.env', original_env_backup)
                print(f"✅ Backed up real .env to {original_env_backup}")
            
            if os.path.exists(test_env_file):
                shutil.copy(test_env_file, '.env')
                print(f"✅ Set up test environment from {test_env_file}")
            
            yield
            
        finally:
            if original_env_backup and os.path.exists(original_env_backup):
                shutil.move(original_env_backup, '.env')
                print("✅ Restored original .env file")
            elif not original_env_backup and os.path.exists('.env'):
                os.remove('.env')
                print("✅ Cleaned up test .env file")
