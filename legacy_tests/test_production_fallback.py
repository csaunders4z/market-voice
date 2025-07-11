#!/usr/bin/env python3
"""
Test Production Fallback Behavior
Verifies that mock data is not used in production mode
"""
import os
import sys
from datetime import datetime
from loguru import logger

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_collection.unified_data_collector import UnifiedDataCollector


def test_production_mode():
    """Test that production mode fails gracefully without mock data"""
    logger.info("=" * 60)
    logger.info("TESTING PRODUCTION MODE FALLBACK")
    logger.info("=" * 60)
    
    try:
        # Create test instance
        test_collector = UnifiedDataCollector()
        test_symbols = ["AAPL", "MSFT", "GOOGL"]
        
        logger.info(f"Testing with symbols: {test_symbols}")
        
        # Simulate all sources failing in production mode
        original_sources = test_collector.sources
        test_collector.sources = [
            ("Failing FMP", lambda x: (False, [], "Rate limited")),
            ("Failing Yahoo", lambda x: (False, [], "Network error")),
            ("Failing Alpha Vantage", lambda x: (False, [], "API error"))
        ]
        
        logger.info("Testing production mode (all sources failing)...")
        result = test_collector.collect_data(test_symbols, production_mode=True)
        
        if not result.get('collection_success'):
            logger.info("✅ Production mode correctly failed when all sources unavailable")
            logger.info(f"  Error: {result.get('error', 'Unknown error')}")
            logger.info("  This is the correct behavior for production!")
        else:
            logger.error("❌ Production mode should have failed!")
            return False
        
        # Test test mode (should use cached data)
        logger.info("\nTesting test mode (should use cached data)...")
        test_result = test_collector.collect_data(test_symbols, production_mode=False)
        
        if test_result.get('collection_success'):
            logger.info("✅ Test mode correctly used cached data")
            logger.info(f"  Data source: {test_result.get('data_source', 'Unknown')}")
            
            summary = test_result.get('market_summary', {})
            logger.info(f"  Total stocks: {summary.get('total_stocks', 0)}")
            logger.info(f"  Data source: {summary.get('data_source', 'Unknown')}")
        else:
            logger.error("❌ Test mode should have succeeded with cached data!")
            return False
        
        # Restore original sources
        test_collector.sources = original_sources
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False


def main():
    """Run the production fallback test"""
    logger.info("Starting Production Fallback Test")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
    
    success = test_production_mode()
    
    if success:
        logger.info("\n🎉 Production fallback behavior is correct!")
        logger.info("✅ Production mode fails gracefully without mock data")
        logger.info("✅ Test mode uses cached data when needed")
    else:
        logger.error("\n❌ Production fallback test failed!")
    
    return success


if __name__ == "__main__":
    success = main()
    print(f"\nTest completed with {'SUCCESS' if success else 'FAILURE'}")
    sys.exit(0 if success else 1) 