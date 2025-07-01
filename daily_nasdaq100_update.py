#!/usr/bin/env python3
"""
Daily NASDAQ-100 Symbol Update Script for Market Voices
Automatically fetches and updates NASDAQ-100 symbols from reliable sources
"""
import sys
import os
from datetime import datetime, timedelta
from loguru import logger
import json

# Add src to path
sys.path.append('src')

from src.data_collection.symbol_updater import SymbolUpdater
from src.data_collection.symbol_loader import SymbolLoader


def setup_logging():
    """Setup logging for the daily update script"""
    logger.remove()  # Remove default handler
    logger.add(
        "logs/daily_nasdaq100_update.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    logger.add(
        sys.stdout,
        level="INFO",
        format="{time:HH:mm:ss} | {level} | {message}"
    )


def check_last_update():
    """Check when the symbols were last updated"""
    try:
        current_file = "src/data_collection/symbol_lists/current_symbols.json"
        if os.path.exists(current_file):
            with open(current_file, 'r') as f:
                data = json.load(f)
                last_updated = data.get('last_updated')
                if last_updated:
                    last_update = datetime.fromisoformat(last_updated)
                    hours_since_update = (datetime.now() - last_update).total_seconds() / 3600
                    logger.info(f"Last update: {last_update.strftime('%Y-%m-%d %H:%M:%S')} ({hours_since_update:.1f} hours ago)")
                    return hours_since_update
        return 24  # Default to 24 hours if no previous update
    except Exception as e:
        logger.warning(f"Could not check last update time: {str(e)}")
        return 24


def run_daily_update():
    """Run the daily NASDAQ-100 symbol update"""
    logger.info("=" * 80)
    logger.info("DAILY NASDAQ-100 SYMBOL UPDATE")
    logger.info("=" * 80)
    logger.info(f"Update timestamp: {datetime.now().isoformat()}")
    
    try:
        # Check if update is needed (run daily)
        hours_since_update = check_last_update()
        if hours_since_update < 12:  # Only update if more than 12 hours have passed
            logger.info(f"Symbols updated recently ({hours_since_update:.1f} hours ago), skipping update")
            return True
        
        # Initialize updater
        updater = SymbolUpdater()
        
        # Fetch current NASDAQ-100 symbols
        logger.info("Fetching current NASDAQ-100 symbols...")
        nasdaq100_symbols = updater.fetch_nasdaq100_symbols()
        
        if not nasdaq100_symbols:
            logger.error("Failed to fetch NASDAQ-100 symbols from any source")
            return False
        
        logger.info(f"Successfully fetched {len(nasdaq100_symbols)} NASDAQ-100 symbols")
        
        # Create comprehensive symbol list
        logger.info("Creating comprehensive symbol list...")
        symbol_data = updater.create_comprehensive_symbol_list()
        
        # Validate the update
        validation_result = validate_update(symbol_data)
        
        if validation_result['success']:
            logger.info("✅ Daily NASDAQ-100 update completed successfully")
            logger.info(f"  Total symbols: {symbol_data['total_symbols']}")
            logger.info(f"  NASDAQ-100 symbols: {symbol_data['nasdaq100_count']}")
            logger.info(f"  S&P 500 symbols: {symbol_data['sp500_count']}")
            logger.info(f"  Symbols in both indices: {len(symbol_data['both_indices'])}")
            
            # Log any warnings
            if validation_result['warnings']:
                logger.warning("Warnings during update:")
                for warning in validation_result['warnings']:
                    logger.warning(f"  - {warning}")
            
            return True
        else:
            logger.error("❌ Daily NASDAQ-100 update failed validation")
            for error in validation_result['errors']:
                logger.error(f"  - {error}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Daily NASDAQ-100 update failed: {str(e)}")
        return False


def validate_update(symbol_data: dict) -> dict:
    """Validate the symbol update results"""
    result = {
        'success': True,
        'warnings': [],
        'errors': []
    }
    
    try:
        # Check NASDAQ-100 count
        nasdaq_count = symbol_data.get('nasdaq100_count', 0)
        if nasdaq_count < 95:
            result['errors'].append(f"NASDAQ-100 count too low: {nasdaq_count} (expected ~100)")
            result['success'] = False
        elif nasdaq_count < 98:
            result['warnings'].append(f"NASDAQ-100 count lower than expected: {nasdaq_count}")
        
        # Check for critical symbols
        critical_symbols = {
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX",
            "ADBE", "CRM", "PYPL", "INTC", "AMD", "QCOM", "AVGO", "TXN"
        }
        
        nasdaq_symbols = set(symbol_data.get('nasdaq100_symbols', []))
        missing_critical = critical_symbols - nasdaq_symbols
        
        if missing_critical:
            result['warnings'].append(f"Missing critical symbols: {missing_critical}")
        
        # Check for duplicates
        all_symbols = symbol_data.get('all_symbols', [])
        if len(all_symbols) != len(set(all_symbols)):
            result['warnings'].append("Duplicate symbols found in combined list")
        
        # Check S&P 500 count
        sp500_count = symbol_data.get('sp500_count', 0)
        if sp500_count < 450:
            result['warnings'].append(f"S&P 500 count lower than expected: {sp500_count}")
        
        return result
        
    except Exception as e:
        result['success'] = False
        result['errors'].append(f"Validation error: {str(e)}")
        return result


def test_symbol_loader():
    """Test the symbol loader with updated symbols"""
    logger.info("Testing symbol loader with updated symbols...")
    
    try:
        loader = SymbolLoader()
        
        # Force refresh
        loader.update_symbols()
        
        # Get symbols
        nasdaq_symbols = loader.get_nasdaq_100_symbols()
        sp500_symbols = loader.get_sp_500_symbols()
        all_symbols = loader.get_all_symbols()
        
        logger.info(f"Symbol loader test results:")
        logger.info(f"  NASDAQ-100 symbols: {len(nasdaq_symbols)}")
        logger.info(f"  S&P 500 symbols: {len(sp500_symbols)}")
        logger.info(f"  Total unique symbols: {len(all_symbols)}")
        
        # Show first 10 NASDAQ symbols
        logger.info(f"  First 10 NASDAQ-100 symbols: {nasdaq_symbols[:10]}")
        
        return True
        
    except Exception as e:
        logger.error(f"Symbol loader test failed: {str(e)}")
        return False


def main():
    """Main function for daily NASDAQ-100 update"""
    # Setup logging
    setup_logging()
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    logger.info("Starting daily NASDAQ-100 symbol update...")
    
    # Run the update
    update_success = run_daily_update()
    
    if update_success:
        # Test the symbol loader
        test_success = test_symbol_loader()
        
        if test_success:
            logger.info("🎉 Daily NASDAQ-100 update completed successfully!")
            return 0
        else:
            logger.error("❌ Symbol loader test failed")
            return 1
    else:
        logger.error("❌ Daily NASDAQ-100 update failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 