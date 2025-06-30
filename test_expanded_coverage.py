#!/usr/bin/env python3
"""
Test Expanded Symbol Coverage for Market Voices
Tests the system with expanded NASDAQ-100 and S&P 500 symbol coverage
"""
import os
import sys
import json
from datetime import datetime
from loguru import logger

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import modules
from src.data_collection.unified_data_collector import UnifiedDataCollector
from src.data_collection.symbol_loader import SymbolLoader
from src.script_generation.script_generator import ScriptGenerator
from src.content_validation.quality_controls import QualityController


def test_expanded_symbol_coverage():
    """Test the expanded symbol coverage with NASDAQ-100 and S&P 500 stocks"""
    logger.info("=" * 80)
    logger.info("TESTING EXPANDED SYMBOL COVERAGE")
    logger.info("=" * 80)
    
    try:
        # Initialize components
        symbol_loader = SymbolLoader()
        unified_collector = UnifiedDataCollector()
        
        # Test symbol loading
        logger.info("Testing symbol loading...")
        nasdaq_symbols = symbol_loader.get_nasdaq_100_symbols()
        sp500_symbols = symbol_loader.get_sp_500_symbols()
        all_symbols = symbol_loader.get_all_symbols()
        
        logger.info(f"Symbol counts:")
        logger.info(f"  NASDAQ-100: {len(nasdaq_symbols)} symbols")
        logger.info(f"  S&P 500: {len(sp500_symbols)} symbols")
        logger.info(f"  Combined unique: {len(all_symbols)} symbols")
        
        # Show sample symbols
        logger.info(f"Sample NASDAQ-100 symbols: {nasdaq_symbols[:10]}")
        logger.info(f"Sample S&P 500 symbols: {sp500_symbols[:10]}")
        
        # Test data collection with expanded symbols
        logger.info("\nTesting data collection with expanded symbols...")
        
        # Use a subset for testing (first 50 symbols)
        test_symbols = all_symbols[:50]
        logger.info(f"Testing with {len(test_symbols)} symbols: {test_symbols[:10]}...")
        
        # Collect data
        market_data = unified_collector.collect_data(symbols=test_symbols, production_mode=False)
        
        if not market_data.get('collection_success'):
            logger.error(f"Data collection failed: {market_data.get('error', 'Unknown error')}")
            return False
        
        # Analyze results
        summary = market_data.get('market_summary', {})
        all_data = market_data.get('all_data', [])
        winners = market_data.get('winners', [])
        losers = market_data.get('losers', [])
        
        logger.info(f"\nData Collection Results:")
        logger.info(f"  Total stocks collected: {len(all_data)}")
        logger.info(f"  Advancing stocks: {summary.get('advancing_stocks', 0)}")
        logger.info(f"  Declining stocks: {summary.get('declining_stocks', 0)}")
        logger.info(f"  Average change: {summary.get('average_change', 0):.2f}%")
        logger.info(f"  Market sentiment: {summary.get('market_sentiment', 'Unknown')}")
        logger.info(f"  Data source: {summary.get('data_source', 'Unknown')}")
        
        # Check winners and losers
        logger.info(f"\nTop Winners:")
        for i, winner in enumerate(winners[:5], 1):
            logger.info(f"  {i}. {winner.get('symbol')}: +{winner.get('percent_change', 0):.2f}% (Volume: {winner.get('volume_ratio', 1):.1f}x)")
        
        logger.info(f"\nTop Losers:")
        for i, loser in enumerate(losers[:5], 1):
            logger.info(f"  {i}. {loser.get('symbol')}: {loser.get('percent_change', 0):.2f}% (Volume: {loser.get('volume_ratio', 1):.1f}x)")
        
        # Check data quality
        stocks_with_tech = [s for s in all_data if s.get('rsi') or s.get('macd_signal')]
        stocks_with_earnings = [s for s in all_data if s.get('earnings_data')]
        stocks_with_analyst = [s for s in all_data if s.get('analyst_data')]
        
        logger.info(f"\nData Quality:")
        logger.info(f"  Stocks with technical indicators: {len(stocks_with_tech)}")
        logger.info(f"  Stocks with earnings data: {len(stocks_with_earnings)}")
        logger.info(f"  Stocks with analyst data: {len(stocks_with_analyst)}")
        
        # Show detailed sample
        if winners:
            sample_winner = winners[0]
            logger.info(f"\nDetailed Sample Winner:")
            logger.info(f"  Symbol: {sample_winner.get('symbol')}")
            logger.info(f"  Company: {sample_winner.get('company_name')}")
            logger.info(f"  Price: ${sample_winner.get('current_price', 0):.2f}")
            logger.info(f"  Change: {sample_winner.get('percent_change', 0):.2f}%")
            logger.info(f"  Volume ratio: {sample_winner.get('volume_ratio', 1):.1f}x")
            logger.info(f"  RSI: {sample_winner.get('rsi', 'N/A')}")
            logger.info(f"  MACD: {sample_winner.get('macd_signal', 'N/A')}")
            
            if sample_winner.get('earnings_data'):
                earnings = sample_winner['earnings_data']
                logger.info(f"  Next earnings: {earnings.get('date', 'N/A')}")
            
            if sample_winner.get('analyst_data'):
                analyst = sample_winner['analyst_data']
                logger.info(f"  Analyst consensus: {analyst.get('consensus', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in expanded symbol coverage test: {str(e)}")
        return False


def test_enhanced_script_generation():
    """Test script generation with expanded data"""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING ENHANCED SCRIPT GENERATION")
    logger.info("=" * 80)
    
    try:
        # Initialize components
        unified_collector = UnifiedDataCollector()
        script_generator = ScriptGenerator()
        
        # Collect data with expanded symbols
        symbol_loader = SymbolLoader()
        all_symbols = symbol_loader.get_all_symbols()
        test_symbols = all_symbols[:30]  # Use 30 symbols for script generation
        
        logger.info(f"Collecting data for script generation with {len(test_symbols)} symbols...")
        market_data = unified_collector.collect_data(symbols=test_symbols, production_mode=False)
        
        if not market_data.get('collection_success'):
            logger.error("Cannot test script generation without market data")
            return False
        
        # Generate script
        logger.info("Generating script with expanded data...")
        script_data = script_generator.generate_script(market_data)
        
        if not script_data.get('generation_success'):
            logger.error(f"Script generation failed: {script_data.get('error', 'Unknown error')}")
            return False
        
        # Analyze script results
        logger.info(f"\nScript Generation Results:")
        logger.info(f"  Lead host: {script_data.get('lead_host', 'Unknown')}")
        logger.info(f"  Estimated runtime: {script_data.get('estimated_runtime_minutes', 0)} minutes")
        
        # Check segments
        winner_segments = script_data.get('winner_segments', [])
        loser_segments = script_data.get('loser_segments', [])
        
        logger.info(f"  Winner segments: {len(winner_segments)}")
        logger.info(f"  Loser segments: {len(loser_segments)}")
        
        # Check quality metrics
        quality_metrics = script_data.get('quality_metrics', {})
        logger.info(f"  Total words: {quality_metrics.get('total_words', 0)}")
        logger.info(f"  Technical indicators used: {quality_metrics.get('technical_indicators_used', 0)}")
        logger.info(f"  News sources referenced: {quality_metrics.get('news_sources_referenced', 0)}")
        
        # Check speaking time balance
        balance = script_data.get('speaking_time_balance', {})
        marcus_pct = balance.get('marcus_percentage', 0)
        suzanne_pct = balance.get('suzanne_percentage', 0)
        logger.info(f"  Speaking time - Marcus: {marcus_pct}%, Suzanne: {suzanne_pct}%")
        
        # Check quality validation
        quality_validation = script_data.get('quality_validation', {})
        overall_score = quality_validation.get('overall_score', 0)
        logger.info(f"  Quality score: {overall_score:.1f}%")
        
        if quality_validation.get('issues'):
            logger.warning(f"  Issues found: {len(quality_validation['issues'])}")
            for issue in quality_validation['issues'][:3]:
                logger.warning(f"    - {issue}")
        
        # Show sample segments
        if winner_segments:
            logger.info(f"\nSample Winner Segment:")
            sample_segment = winner_segments[0]
            logger.info(f"  Stock: {sample_segment.get('stock', 'Unknown')}")
            logger.info(f"  Host: {sample_segment.get('host', 'Unknown')}")
            logger.info(f"  Text preview: {sample_segment.get('text', '')[:150]}...")
        
        if loser_segments:
            logger.info(f"\nSample Loser Segment:")
            sample_segment = loser_segments[0]
            logger.info(f"  Stock: {sample_segment.get('stock', 'Unknown')}")
            logger.info(f"  Host: {sample_segment.get('host', 'Unknown')}")
            logger.info(f"  Text preview: {sample_segment.get('text', '')[:150]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in enhanced script generation test: {str(e)}")
        return False


def test_quality_validation():
    """Test quality validation with expanded data"""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING QUALITY VALIDATION")
    logger.info("=" * 80)
    
    try:
        quality_controller = QualityController()
        
        # Create a comprehensive test script
        test_script = {
            "intro": "Welcome to Market Voices! I'm Marcus, and today we're breaking down the expanded NASDAQ-100 and S&P 500 performance with my colleague Suzanne. We've analyzed over 200 stocks today, giving us a comprehensive view of the market.",
            "market_overview": "Today's session showed remarkable breadth across the expanded universe of stocks we're now covering. With our enhanced data collection covering both NASDAQ-100 and S&P 500 constituents, we're seeing sector rotation patterns that weren't visible with our previous limited scope.",
            "winner_segments": [
                {
                    "host": "marcus",
                    "stock": "AAPL",
                    "text": "Apple Inc. surged 2.5% today, driven by multiple catalysts. First, the company announced a major AI partnership that positions it at the forefront of the AI revolution. Second, analysts from Goldman Sachs raised their price target citing strong iPhone demand and services growth. Third, the technical indicators show a bullish MACD crossover with RSI at 65, indicating momentum without overbought conditions. Volume was 2.3 times the average, suggesting institutional accumulation. This move reflects broader market rotation into quality tech names as investors seek AI exposure."
                },
                {
                    "host": "suzanne",
                    "stock": "MSFT",
                    "text": "Microsoft Corporation gained 1.8% today, continuing its strong performance. The catalyst was the company's Azure cloud division reporting 30% year-over-year growth, exceeding analyst expectations. Additionally, the company's AI initiatives are gaining traction, with Azure OpenAI Service seeing record adoption. Technical analysis shows the stock breaking out of a consolidation pattern with strong volume confirmation. Analysts from Morgan Stanley have upgraded their rating, citing the company's dominant position in enterprise software and cloud services."
                }
            ],
            "loser_segments": [
                {
                    "host": "suzanne",
                    "stock": "TSLA",
                    "text": "Tesla Inc. declined 1.2% today, underperforming the broader market. The drop was primarily driven by regulatory concerns as the NHTSA expanded its investigation into Autopilot safety. Additionally, competition in the EV space is intensifying, with traditional automakers launching competitive models. Technical indicators show the stock testing support levels with RSI at 35, indicating oversold conditions. However, volume was below average, suggesting limited selling pressure. Analysts remain divided on the stock's prospects given the regulatory headwinds."
                }
            ],
            "market_sentiment": "Overall market sentiment remains positive despite some volatility. The expanded coverage reveals sector rotation patterns that suggest institutional investors are positioning for continued economic growth while managing risk through diversification.",
            "outro": "This concludes today's Market Voices analysis. Thanks for joining us as we continue to provide comprehensive coverage of the expanded NASDAQ-100 and S&P 500 universe. This is Marcus, signing off."
        }
        
        # Run quality validation
        validation_results = quality_controller.validate_script_quality(test_script)
        
        logger.info(f"Quality Validation Results:")
        logger.info(f"  Overall score: {validation_results.get('overall_score', 0):.1f}%")
        logger.info(f"  Passed checks: {len(validation_results.get('passed_checks', []))}")
        logger.info(f"  Issues found: {len(validation_results.get('issues', []))}")
        logger.info(f"  Warnings: {len(validation_results.get('warnings', []))}")
        
        if validation_results.get('passed_checks'):
            logger.info(f"\nPassed Checks:")
            for check in validation_results['passed_checks'][:5]:
                logger.info(f"  ✓ {check}")
        
        if validation_results.get('issues'):
            logger.warning(f"\nIssues Found:")
            for issue in validation_results['issues'][:5]:
                logger.warning(f"  - {issue}")
        
        if validation_results.get('warnings'):
            logger.warning(f"\nWarnings:")
            for warning in validation_results['warnings'][:5]:
                logger.warning(f"  - {warning}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in quality validation test: {str(e)}")
        return False


def main():
    """Run all tests"""
    logger.info("Starting Expanded Coverage Tests")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Set test mode
    os.environ["TEST_MODE"] = "1"
    
    # Run tests
    tests = [
        ("Expanded Symbol Coverage", test_expanded_symbol_coverage),
        ("Enhanced Script Generation", test_enhanced_script_generation),
        ("Quality Validation", test_quality_validation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results[test_name] = "PASSED" if success else "FAILED"
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {str(e)}")
            results[test_name] = "FAILED"
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result == "PASSED" else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    passed_count = sum(1 for result in results.values() if result == "PASSED")
    total_count = len(results)
    
    logger.info(f"\nOverall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        logger.info("🎉 All tests passed! Expanded coverage is working correctly.")
    else:
        logger.warning("⚠️  Some tests failed. Please review the logs above.")
    
    return passed_count == total_count


if __name__ == "__main__":
    main() 