#!/usr/bin/env python3
"""
Quick Fallback Test - No API Calls
Tests the fallback logic without hitting rate limits
"""
import os
import sys
from datetime import datetime
from loguru import logger

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_collection.unified_data_collector import UnifiedDataCollector


def test_fallback_logic():
    """Test fallback logic without API calls"""
    logger.info("=" * 50)
    logger.info("TESTING FALLBACK LOGIC (NO API CALLS)")
    logger.info("=" * 50)
    
    try:
        # Create a test instance
        test_collector = UnifiedDataCollector()
        
        # Test symbols
        test_symbols = ["AAPL", "MSFT", "GOOGL"]
        
        logger.info(f"Testing with symbols: {test_symbols}")
        
        # Simulate all sources failing by replacing them with failing functions
        original_sources = test_collector.sources
        test_collector.sources = [
            ("Failing FMP", lambda x: (False, [], "Rate limited")),
            ("Failing Yahoo", lambda x: (False, [], "Network error")),
            ("Failing Alpha Vantage", lambda x: (False, [], "API error"))
        ]
        
        logger.info("Testing fallback to mock data...")
        result = test_collector.collect_data(test_symbols)
        
        if result.get('collection_success'):
            logger.info("✅ Fallback to mock data successful!")
            logger.info(f"  Data source: {result.get('data_source', 'Unknown')}")
            
            summary = result.get('market_summary', {})
            logger.info(f"  Total stocks: {summary.get('total_stocks', 0)}")
            logger.info(f"  Advancing: {summary.get('advancing_stocks', 0)}")
            logger.info(f"  Declining: {summary.get('declining_stocks', 0)}")
            
            all_data = result.get('all_data', [])
            if all_data:
                logger.info(f"\nMock data sample:")
                for stock in all_data[:2]:
                    logger.info(f"  {stock.get('symbol')}: {stock.get('percent_change', 0):.2f}%")
            
            # Restore original sources
            test_collector.sources = original_sources
            return True
        else:
            logger.error("❌ Fallback failed!")
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False


def main():
    """Run the quick fallback test"""
    logger.info("Starting Quick Fallback Test")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
    
    success = test_fallback_logic()
    
    if success:
        logger.info("\n🎉 Fallback system is working correctly!")
        logger.info("The system can handle API failures gracefully.")
    else:
        logger.error("\n❌ Fallback system test failed!")
    
    return success


if __name__ == "__main__":
    success = main()
    print(f"\nTest completed with {'SUCCESS' if success else 'FAILURE'}")
    sys.exit(0 if success else 1) 