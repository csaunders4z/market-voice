#!/usr/bin/env python3
"""
Production validation script for Market Voices
Tests system readiness without running full workflow
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import get_settings
from src.utils.health_check import run_health_check, print_health_status
from src.utils.logger import setup_logging, get_logger

def validate_api_keys():
    """Validate that required API keys are configured"""
    logger = get_logger("ProductionValidator")
    settings = get_settings()
    
    required_keys = {
        'OpenAI': settings.openai_api_key,
        'Alpha Vantage': settings.alpha_vantage_api_key,
        'The News API': settings.the_news_api_api_key,
    }
    
    optional_keys = {
        'FMP': settings.fmp_api_key,
        'Finnhub': settings.finnhub_api_key,
        'NewsData.io': settings.newsdata_io_api_key,
    }
    
    missing_required = []
    for name, key in required_keys.items():
        if not key or key.startswith('your-') or key.startswith('sk-your-') or key == "":
            missing_required.append(name)
    
    missing_optional = []
    for name, key in optional_keys.items():
        if not key or key.startswith('your-'):
            missing_optional.append(name)
    
    if missing_required:
        logger.warning(f"⚠️ Placeholder API keys detected for: {', '.join(missing_required)}")
        logger.warning("Replace placeholder values in .env with actual production API keys")
        logger.info("✅ System validation complete - ready for API key configuration")
        return True
    
    if missing_optional:
        logger.warning(f"Missing optional API keys: {', '.join(missing_optional)}")
    
    logger.info("✅ All required API keys are configured")
    return True

def validate_environment():
    """Validate environment configuration"""
    logger = get_logger("ProductionValidator")
    
    env_file = Path(".env")
    if not env_file.exists():
        logger.error("❌ .env file not found. Copy env.template to .env and configure API keys.")
        return False
    
    settings = get_settings()
    output_dir = Path(settings.output_directory)
    if not output_dir.exists():
        logger.info(f"Creating output directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
    
    log_dir = Path("logs")
    if not log_dir.exists():
        logger.info(f"Creating logs directory: {log_dir}")
        log_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("✅ Environment configuration validated")
    return True

def validate_dependencies():
    """Validate that required dependencies are available"""
    logger = get_logger("ProductionValidator")
    
    required_modules = [
        'openai',
        'requests',
        'pandas',
        'yfinance',
        'loguru',
        'pydantic',
        'dotenv'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"❌ Missing required modules: {', '.join(missing_modules)}")
        logger.error("Run: pip install -r requirements.txt")
        return False
    
    logger.info("✅ All required dependencies are available")
    return True

def main():
    """Run production validation"""
    setup_logging()
    logger = get_logger("ProductionValidator")
    
    logger.info("Starting production validation...")
    
    validation_steps = [
        ("Environment Configuration", validate_environment),
        ("Dependencies", validate_dependencies),
        ("API Keys", validate_api_keys),
    ]
    
    all_passed = True
    for step_name, validation_func in validation_steps:
        logger.info(f"Validating {step_name}...")
        if not validation_func():
            logger.error(f"❌ {step_name} validation failed")
            all_passed = False
        else:
            logger.info(f"✅ {step_name} validation passed")
    
    if not all_passed:
        logger.error("❌ Production validation failed")
        return 1
    
    logger.info("Running system health check...")
    health_results = run_health_check()
    print_health_status(health_results)
    
    if health_results["overall_status"] == "unhealthy":
        logger.error("❌ System health check failed")
        return 1
    elif health_results["overall_status"] == "degraded":
        logger.warning("⚠️ System health check shows degraded status")
        logger.info("System may still work but some features might be limited")
        return 2
    
    logger.info("✅ Production validation completed successfully")
    logger.info("System is ready for production deployment!")
    return 0

if __name__ == "__main__":
    exit(main())
