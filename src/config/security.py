"""
Security configuration for Market Voices
Handles secrets management, file permissions, and security settings
"""
import os
import stat
from pathlib import Path
from typing import Optional
from loguru import logger


class SecurityConfig:
    """Security configuration and utilities"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.env_file = self.base_dir / ".env"
        self.output_dir = self.base_dir / "output"
        self.logs_dir = self.base_dir / "logs"
        
    def secure_env_file(self) -> bool:
        """Ensure .env file has secure permissions (600)"""
        try:
            if self.env_file.exists():
                # Set permissions to owner read/write only
                self.env_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
                logger.info(f"Secured .env file permissions: {oct(self.env_file.stat().st_mode)[-3:]}")
                return True
            else:
                logger.warning(".env file not found")
                return False
        except Exception as e:
            logger.error(f"Failed to secure .env file: {str(e)}")
            return False
    
    def secure_output_directories(self) -> bool:
        """Ensure output and logs directories have appropriate permissions"""
        try:
            for directory in [self.output_dir, self.logs_dir]:
                if directory.exists():
                    # Set permissions to owner read/write/execute, group read/execute
                    directory.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | 
                                  stat.S_IRGRP | stat.S_IXGRP)
                    logger.info(f"Secured directory permissions for {directory.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to secure output directories: {str(e)}")
            return False
    
    def validate_secrets_not_logged(self) -> bool:
        """Validate that no secrets are being logged"""
        try:
            # Check if any environment variables contain sensitive data
            sensitive_vars = [
                'OPENAI_API_KEY', 'FMP_API_KEY', 'NEWS_API_KEY', 
                'NEWSDATA_IO_API_KEY', 'THE_NEWS_API_API_KEY', 'BIZTOC_API_KEY'
            ]
            
            for var in sensitive_vars:
                value = os.getenv(var)
                if value and len(value) > 10:  # If it's a real key (not placeholder)
                    # Check if it appears in any log files
                    log_files = list(self.logs_dir.glob("*.log"))
                    for log_file in log_files:
                        with open(log_file, 'r') as f:
                            content = f.read()
                            if value in content:
                                logger.error(f"SECURITY ALERT: API key found in log file {log_file}")
                                return False
            return True
        except Exception as e:
            logger.error(f"Failed to validate secrets logging: {str(e)}")
            return False
    
    def check_file_permissions(self) -> dict:
        """Check file permissions for security"""
        results = {
            'env_file_secure': False,
            'output_dirs_secure': False,
            'no_secrets_in_logs': False
        }
        
        try:
            # Check .env file permissions
            if self.env_file.exists():
                mode = self.env_file.stat().st_mode
                results['env_file_secure'] = (
                    mode & stat.S_IRWXG == 0 and  # No group write/execute
                    mode & stat.S_IRWXO == 0      # No others read/write/execute
                )
            
            # Check output directories
            secure_dirs = True
            for directory in [self.output_dir, self.logs_dir]:
                if directory.exists():
                    mode = directory.stat().st_mode
                    # Should not be world-writable
                    if mode & stat.S_IWOTH:
                        secure_dirs = False
            
            results['output_dirs_secure'] = secure_dirs
            results['no_secrets_in_logs'] = self.validate_secrets_not_logged()
            
        except Exception as e:
            logger.error(f"Failed to check file permissions: {str(e)}")
        
        return results
    
    def run_security_audit(self) -> dict:
        """Run comprehensive security audit"""
        logger.info("Starting security audit...")
        
        audit_results = {
            'file_permissions': self.check_file_permissions(),
            'env_file_exists': self.env_file.exists(),
            'env_file_tracked': self._is_env_tracked_by_git(),
            'recommendations': []
        }
        
        # Generate recommendations
        if not audit_results['file_permissions']['env_file_secure']:
            audit_results['recommendations'].append(
                "Secure .env file permissions (should be 600)"
            )
        
        if not audit_results['file_permissions']['output_dirs_secure']:
            audit_results['recommendations'].append(
                "Secure output directories (should not be world-writable)"
            )
        
        if audit_results['env_file_tracked']:
            audit_results['recommendations'].append(
                "CRITICAL: .env file is tracked by git - remove immediately!"
            )
        
        if not audit_results['file_permissions']['no_secrets_in_logs']:
            audit_results['recommendations'].append(
                "CRITICAL: API keys found in log files - review logging configuration"
            )
        
        logger.info("Security audit completed")
        return audit_results
    
    def _is_env_tracked_by_git(self) -> bool:
        """Check if .env file is tracked by git"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'ls-files', '.env'], 
                capture_output=True, 
                text=True, 
                cwd=self.base_dir
            )
            return bool(result.stdout.strip())
        except Exception:
            return False


# Global instance
security_config = SecurityConfig() 