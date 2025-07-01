#!/usr/bin/env python3
"""
Test comprehensive data collection for Market Voices
Verifies collection of price data for ALL NASDAQ-100 and S&P-500 stocks
"""
import sys
import os
from datetime import datetime
from loguru import logger

# Add src to path
sys.path.append('src')

from src.data_collection.comprehensive_collector import comprehensive_collector


def main():
    """Test comprehensive data collection"""
    logger.info("=" * 80)
    logger.info("TESTING COMPREHENSIVE DATA COLLECTION")
    logger.info("=" * 80)
    logger.info("This test will collect price data for ALL NASDAQ-100 and S&P-500 stocks")
    logger.info(f"Test timestamp: {datetime.now().isoformat()}")
    
    try:
        # Test comprehensive collection
        logger.info("\n📊 Starting comprehensive data collection...")
        start_time = datetime.now()
        
        result = comprehensive_collector.collect_comprehensive_data(production_mode=True)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if result.get('collection_success'):
            logger.info("\n✅ Comprehensive data collection successful!")
            
            # Display results
            market_summary = result.get('market_summary', {})
            coverage_stats = result.get('coverage_stats', {})
            
            logger.info(f"📈 Collection Results:")
            logger.info(f"   Data source: {result.get('data_source', 'Unknown')}")
            logger.info(f"   Duration: {duration:.1f} seconds")
            logger.info(f"   Total stocks collected: {market_summary.get('total_stocks_analyzed', 0)}")
            logger.info(f"   Target symbols: {market_summary.get('total_target_symbols', 0)}")
            
            logger.info(f"\n📊 Coverage Statistics:")
            logger.info(f"   Overall coverage: {coverage_stats.get('coverage_percentage', 0):.1f}%")
            logger.info(f"   S&P 500 coverage: {coverage_stats.get('sp500_coverage', 0)} stocks")
            logger.info(f"   NASDAQ-100 coverage: {coverage_stats.get('nasdaq100_coverage', 0)} stocks")
            
            logger.info(f"\n📈 Market Summary:")
            logger.info(f"   Advancing stocks: {market_summary.get('advancing_stocks', 0)}")
            logger.info(f"   Declining stocks: {market_summary.get('declining_stocks', 0)}")
            logger.info(f"   Average change: {market_summary.get('average_change', 0):.2f}%")
            logger.info(f"   Market sentiment: {market_summary.get('market_sentiment', 'Unknown')}")
            
            # Display top winners and losers
            winners = result.get('winners', [])
            losers = result.get('losers', [])
            
            logger.info(f"\n🏆 Top Winners:")
            for i, winner in enumerate(winners[:5], 1):
                logger.info(f"   {i}. {winner['symbol']}: {winner['percent_change']:+.2f}%")
            
            logger.info(f"\n📉 Top Losers:")
            for i, loser in enumerate(losers[:5], 1):
                logger.info(f"   {i}. {loser['symbol']}: {loser['percent_change']:+.2f}%")
            
            # Check if we have sufficient data for script generation
            if len(winners) >= 3 and len(losers) >= 1:
                logger.info(f"\n✅ Sufficient data for script generation!")
                logger.info(f"   Winners: {len(winners)} (need 3+)")
                logger.info(f"   Losers: {len(losers)} (need 1+)")
            else:
                logger.warning(f"\n⚠️  Insufficient data for script generation!")
                logger.warning(f"   Winners: {len(winners)} (need 3+)")
                logger.warning(f"   Losers: {len(losers)} (need 1+)")
            
            # Check coverage quality
            coverage_pct = coverage_stats.get('coverage_percentage', 0)
            if coverage_pct >= 90:
                logger.info(f"\n🎉 Excellent coverage: {coverage_pct:.1f}%")
            elif coverage_pct >= 80:
                logger.info(f"\n✅ Good coverage: {coverage_pct:.1f}%")
            elif coverage_pct >= 70:
                logger.warning(f"\n⚠️  Moderate coverage: {coverage_pct:.1f}%")
            else:
                logger.error(f"\n❌ Poor coverage: {coverage_pct:.1f}%")
            
        else:
            logger.error("\n❌ Comprehensive data collection failed!")
            logger.error(f"   Error: {result.get('error', 'Unknown error')}")
            
            if result.get('critical_errors'):
                logger.error(f"   Critical errors: {result.get('critical_errors')}")
        
        logger.info(f"\n" + "=" * 80)
        logger.info("COMPREHENSIVE DATA COLLECTION TEST COMPLETED")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main() 