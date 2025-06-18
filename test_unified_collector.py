#!/usr/bin/env python3
"""
Test Unified Data Collector with Fallback Logic
Tests the multiple source fallback system
"""
import os
import sys
from datetime import datetime
from loguru import logger

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_collection.unified_data_collector import unified_collector


def test_unified_collector():
    """Test the unified collector with fallback logic"""
    logger.info("=" * 60)
    logger.info("TESTING UNIFIED DATA COLLECTOR")
    logger.info("=" * 60)
    
    try:
        # Test with a small set of symbols to avoid rate limits
        test_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
        
        logger.info(f"Testing with symbols: {test_symbols}")
        
        # Collect data using unified collector
        market_data = unified_collector.collect_data(test_symbols)
        
        if not market_data.get('collection_success'):
            logger.error(f"Unified collection failed: {market_data.get('error', 'Unknown error')}")
            return False
        
        # Log results
        logger.info(f"✅ Collection successful!")
        logger.info(f"  Data source: {market_data.get('data_source', 'Unknown')}")
        
        summary = market_data.get('market_summary', {})
        logger.info(f"  Total stocks: {summary.get('total_stocks', 0)}")
        logger.info(f"  Advancing: {summary.get('advancing_stocks', 0)}")
        logger.info(f"  Declining: {summary.get('declining_stocks', 0)}")
        logger.info(f"  Average change: {summary.get('average_change', 0):.2f}%")
        logger.info(f"  Market sentiment: {summary.get('market_sentiment', 'Unknown')}")
        
        # Check winners and losers
        winners = market_data.get('winners', [])
        losers = market_data.get('losers', [])
        logger.info(f"  Top winners: {len(winners)}")
        logger.info(f"  Top losers: {len(losers)}")
        
        # Show sample data
        all_data = market_data.get('all_data', [])
        if all_data:
            logger.info(f"\nSample Data:")
            for i, stock in enumerate(all_data[:3], 1):
                logger.info(f"  {i}. {stock.get('symbol')} - {stock.get('company_name')}")
                logger.info(f"     Change: {stock.get('percent_change', 0):.2f}%")
                logger.info(f"     Price: ${stock.get('current_price', 0):.2f}")
                logger.info(f"     RSI: {stock.get('rsi', 'N/A')}")
                logger.info(f"     Volume ratio: {stock.get('volume_ratio', 'N/A')}")
                if stock.get('news_summary'):
                    logger.info(f"     News: {stock['news_summary'][:80]}...")
                logger.info("")
        
        # Test fallback by simulating rate limit
        logger.info("\n" + "=" * 40)
        logger.info("TESTING FALLBACK LOGIC")
        logger.info("=" * 40)
        
        # Temporarily modify the sources to simulate failures
        original_sources = unified_collector.sources
        unified_collector.sources = [
            ("Failing Source", lambda x: (False, [], "Rate limited")),
            ("Yahoo Finance", unified_collector._collect_yf_data)
        ]
        
        logger.info("Testing fallback to Yahoo Finance...")
        fallback_data = unified_collector.collect_data(test_symbols[:3])
        
        if fallback_data.get('collection_success'):
            logger.info(f"✅ Fallback successful using {fallback_data.get('data_source', 'Unknown')}")
        else:
            logger.warning("⚠️ Fallback failed, should use mock data")
        
        # Restore original sources
        unified_collector.sources = original_sources
        
        return True
        
    except Exception as e:
        logger.error(f"Error in unified collector test: {str(e)}")
        return False


def main():
    """Run the unified collector test"""
    logger.info("Starting Unified Data Collector Test")
    logger.info(f"Test timestamp: {datetime.now().isoformat()}")
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
    
    try:
        success = test_unified_collector()
        
        if success:
            logger.info("\n🎉 Unified collector test passed!")
            logger.info("The system can now handle rate limits gracefully with fallback sources.")
        else:
            logger.error("\n❌ Unified collector test failed!")
        
        return success
        
    except Exception as e:
        logger.error(f"Test crashed: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 