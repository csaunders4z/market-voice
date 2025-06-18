"""
Logging configuration for Market Voices
"""
import sys
import os
from pathlib import Path
from loguru import logger

from ..config.settings import get_settings


def setup_logging():
    """Setup logging configuration for the application"""
    
    # Remove default logger
    logger.remove()
    
    # Create logs directory if it doesn't exist
    log_file = Path(get_settings().log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Add console logger
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=get_settings().log_level,
        colorize=True
    )
    
    # Add file logger
    logger.add(
        get_settings().log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=get_settings().log_level,
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )
    
    logger.info("Logging setup completed")
    logger.info(f"Log level: {get_settings().log_level}")
    logger.info(f"Log file: {get_settings().log_file}")


def get_logger(name: str = ""):
    """Get a logger instance"""
    if name:
        return logger.bind(name=name)
    return logger 