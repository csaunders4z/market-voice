"""
Enhanced logging configuration for Market Voices
Includes log rotation, security features, and structured logging
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger


class SecureLoggingConfig:
    """Secure logging configuration with rotation and filtering"""
    
    def __init__(self):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Sensitive patterns to filter from logs
        self.sensitive_patterns = [
            r'api[_-]?key["\']?\s*[:=]\s*["\'][^"\']+["\']',
            r'secret["\']?\s*[:=]\s*["\'][^"\']+["\']',
            r'token["\']?\s*[:=]\s*["\'][^"\']+["\']',
            r'password["\']?\s*[:=]\s*["\'][^"\']+["\']',
            r'credential["\']?\s*[:=]\s*["\'][^"\']+["\']',
        ]
        
    def filter_sensitive_data(self, record):
        """Filter sensitive data from log records"""
        import re
        
        # Check if message contains sensitive data
        message = str(record["message"])
        for pattern in self.sensitive_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                # Replace with placeholder
                message = re.sub(pattern, '[SENSITIVE_DATA_FILTERED]', message, flags=re.IGNORECASE)
        
        # Check if extra fields contain sensitive data
        for key, value in record["extra"].items():
            if isinstance(value, str):
                for pattern in self.sensitive_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        record["extra"][key] = '[SENSITIVE_DATA_FILTERED]'
        
        record["message"] = message
        return record
    
    def setup_logging(self, log_level: str = "INFO", enable_file_logging: bool = True):
        """Setup secure logging configuration"""
        
        # Remove default logger
        logger.remove()
        
        # Add console logger with filtering
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            filter=self.filter_sensitive_data,
            colorize=True
        )
        
        if enable_file_logging:
            # Add file logger with rotation
            log_file = self.logs_dir / "market_voices.log"
            
            logger.add(
                log_file,
                level=log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                filter=self.filter_sensitive_data,
                rotation="10 MB",  # Rotate when file reaches 10MB
                retention="30 days",  # Keep logs for 30 days
                compression="gz",  # Compress rotated logs
                backtrace=True,
                diagnose=True,
                enqueue=True  # Thread-safe logging
            )
            
            # Add error log file
            error_log_file = self.logs_dir / "market_voices_errors.log"
            logger.add(
                error_log_file,
                level="ERROR",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                filter=self.filter_sensitive_data,
                rotation="5 MB",
                retention="90 days",
                compression="gz",
                backtrace=True,
                diagnose=True,
                enqueue=True
            )
        
        logger.info("Secure logging setup completed")
        logger.info(f"Log level: {log_level}")
        logger.info(f"File logging: {'enabled' if enable_file_logging else 'disabled'}")
    
    def cleanup_old_logs(self, days: int = 30):
        """Clean up old log files"""
        try:
            import time
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            
            for log_file in self.logs_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    logger.info(f"Cleaned up old log file: {log_file}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {str(e)}")
    
    def get_log_stats(self) -> dict:
        """Get logging statistics"""
        stats = {
            'total_log_files': 0,
            'total_size_mb': 0,
            'oldest_log': None,
            'newest_log': None
        }
        
        try:
            log_files = list(self.logs_dir.glob("*.log*"))
            stats['total_log_files'] = len(log_files)
            
            if log_files:
                total_size = sum(f.stat().st_size for f in log_files)
                stats['total_size_mb'] = round(total_size / (1024 * 1024), 2)
                
                # Find oldest and newest logs
                times = [(f, f.stat().st_mtime) for f in log_files]
                oldest = min(times, key=lambda x: x[1])
                newest = max(times, key=lambda x: x[1])
                
                stats['oldest_log'] = datetime.fromtimestamp(oldest[1]).isoformat()
                stats['newest_log'] = datetime.fromtimestamp(newest[1]).isoformat()
                
        except Exception as e:
            logger.error(f"Failed to get log stats: {str(e)}")
        
        return stats


# Global instance
secure_logging = SecureLoggingConfig() 