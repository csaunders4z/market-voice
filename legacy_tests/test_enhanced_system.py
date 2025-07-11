#!/usr/bin/env python3
"""
Enhanced System Test for Market Voices
Tests the complete workflow with quality improvements
"""
import os
import sys
import json
from datetime import datetime
from loguru import logger

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import modules using absolute imports
from src.data_collection.stock_data import stock_collector
from src.script_generation.script_generator import script_generator
from src.content_validation.quality_controls import quality_controller


def test_enhanced_data_collection():
    """Test enhanced data collection with technical indicators and news"""
    logger.info("=" * 60)
    logger.info("TESTING ENHANCED DATA COLLECTION")
    logger.info("=" * 60)
    
    try:
        # Check if we're in quick test mode
        quick_test = os.getenv("QUICK_TEST") == "1"
        if quick_test:
            logger.info("Running in QUICK_TEST mode - limited scope")
            # Use a smaller subset for quick testing
            original_symbols = fmp_stock_collector.symbols
            fmp_stock_collector.symbols = original_symbols[:5]  # Only test first 5 symbols
            logger.info(f"Testing with {len(fmp_stock_collector.symbols)} symbols: {fmp_stock_collector.symbols}")
        
        logger.info("Starting data collection...")
        # Collect enhanced data
        market_data = stock_collector.collect_enhanced_data()
        
        if not market_data.get('collection_success'):
            logger.error(f"Data collection failed: {market_data.get('error', 'Unknown error')}")
            return False
        
        logger.info("Data collection completed successfully!")
        
        # Log results
        summary = market_data.get('market_summary', {})
        logger.info(f"Data Collection Results:")
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
        
        # Check technical indicators
        all_data = market_data.get('all_data', [])
        stocks_with_tech = [s for s in all_data if s.get('rsi') or s.get('macd_signal')]
        logger.info(f"  Stocks with technical indicators: {len(stocks_with_tech)}")
        
        # Check news integration
        news_data = market_data.get('news_data', {})
        news_summaries = news_data.get('news_summaries', {})
        logger.info(f"  News summaries: {len(news_summaries)}")
        
        # Show sample data
        if winners:
            sample_winner = winners[0]
            logger.info(f"\nSample Winner Data:")
            logger.info(f"  Symbol: {sample_winner.get('symbol')}")
            logger.info(f"  Company: {sample_winner.get('company_name')}")
            logger.info(f"  Change: {sample_winner.get('percent_change', 0):.2f}%")
            logger.info(f"  RSI: {sample_winner.get('rsi', 'N/A')}")
            logger.info(f"  MACD: {sample_winner.get('macd_signal', 'N/A')}")
            logger.info(f"  Volume ratio: {sample_winner.get('volume_ratio', 'N/A')}")
            if sample_winner.get('news_summary'):
                logger.info(f"  News: {sample_winner['news_summary'][:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in enhanced data collection test: {str(e)}")
        return False


def test_enhanced_script_generation():
    """Test enhanced script generation with quality validation"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING ENHANCED SCRIPT GENERATION")
    logger.info("=" * 60)
    
    try:
        # First collect data
        market_data = stock_collector.collect_enhanced_data()
        
        if not market_data.get('collection_success'):
            logger.error("Cannot test script generation without market data")
            return False
        
        # Generate script
        script_data = script_generator.generate_script(market_data)
        
        if not script_data.get('generation_success'):
            logger.error(f"Script generation failed: {script_data.get('error', 'Unknown error')}")
            return False
        
        # Log script results
        logger.info(f"Script Generation Results:")
        logger.info(f"  Lead host: {script_data.get('lead_host', 'Unknown')}")
        logger.info(f"  Segments: {len(script_data.get('segments', []))}")
        logger.info(f"  Estimated runtime: {script_data.get('estimated_runtime_minutes', 0)} minutes")
        
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
            for issue in quality_validation['issues'][:3]:  # Show first 3
                logger.warning(f"    - {issue}")
        
        if quality_validation.get('warnings'):
            logger.warning(f"  Warnings: {len(quality_validation['warnings'])}")
            for warning in quality_validation['warnings'][:3]:  # Show first 3
                logger.warning(f"    - {warning}")
        
        if quality_validation.get('passed_checks'):
            logger.info(f"  Passed checks: {len(quality_validation['passed_checks'])}")
            for check in quality_validation['passed_checks'][:3]:  # Show first 3
                logger.info(f"    ✓ {check}")
        
        # Show sample segments
        segments = script_data.get('segments', [])
        if segments:
            logger.info(f"\nSample Segments:")
            for i, segment in enumerate(segments[:3], 1):
                logger.info(f"  Segment {i} - {segment.get('host', 'Unknown').title()}:")
                logger.info(f"    Topic: {segment.get('topic', 'N/A')}")
                logger.info(f"    Words: {segment.get('word_count', 0)}")
                logger.info(f"    Text: {segment.get('text', '')[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in enhanced script generation test: {str(e)}")
        return False


def test_quality_validation():
    """Test quality validation independently"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING QUALITY VALIDATION")
    logger.info("=" * 60)
    
    try:
        # Create a sample script for testing
        sample_script = {
            "intro": "Welcome to Market Voices! I'm Marcus, and today we're breaking down the NASDAQ-100 performance with my colleague Suzanne.",
            "segments": [
                {
                    "host": "marcus",
                    "text": "Today was an interesting session for the NASDAQ-100. We saw strong performance from technology stocks as investors remain optimistic about AI and cloud computing growth. Apple and Microsoft led the charge with solid gains.",
                    "topic": "Market Overview"
                },
                {
                    "host": "suzanne",
                    "text": "Looking at the technical indicators, we're seeing some interesting patterns. RSI levels are showing overbought conditions for several stocks, while MACD crossovers suggest continued momentum.",
                    "topic": "Technical Analysis"
                },
                {
                    "host": "marcus",
                    "text": "The market is showing resilience despite some volatility. Volume was healthy, and institutional buying patterns suggest continued confidence in the tech sector's long-term prospects.",
                    "topic": "Market Sentiment"
                }
            ],
            "outro": "This wraps up today's Market Voices analysis. Thanks for joining us, and don't forget to subscribe for daily market insights. This is Marcus, signing off."
        }
        
        # Run quality validation
        validation_results = quality_controller.validate_script_quality(sample_script)
        
        # Log results
        logger.info(f"Quality Validation Results:")
        logger.info(f"  Overall score: {validation_results.get('overall_score', 0):.1f}%")
        
        if validation_results.get('issues'):
            logger.warning(f"  Issues: {len(validation_results['issues'])}")
            for issue in validation_results['issues']:
                logger.warning(f"    - {issue}")
        
        if validation_results.get('warnings'):
            logger.warning(f"  Warnings: {len(validation_results['warnings'])}")
            for warning in validation_results['warnings']:
                logger.warning(f"    - {warning}")
        
        if validation_results.get('passed_checks'):
            logger.info(f"  Passed checks: {len(validation_results['passed_checks'])}")
            for check in validation_results['passed_checks']:
                logger.info(f"    ✓ {check}")
        
        # Get improvement suggestions
        suggestions = quality_controller.suggest_improvements(validation_results)
        if suggestions:
            logger.info(f"\nImprovement Suggestions:")
            for suggestion in suggestions:
                logger.info(f"  - {suggestion}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in quality validation test: {str(e)}")
        return False


def test_simple_validation():
    """Test quality validation with mock data (no API calls)"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING SIMPLE VALIDATION (NO API CALLS)")
    logger.info("=" * 60)
    
    try:
        # Create mock market data
        mock_market_data = {
            'market_summary': {
                'total_stocks': 5,
                'advancing_stocks': 3,
                'declining_stocks': 2,
                'average_change': 1.5,
                'market_sentiment': 'Bullish',
                'market_date': datetime.now().isoformat()
            },
            'winners': [
                {
                    'symbol': 'AAPL',
                    'company_name': 'Apple Inc.',
                    'current_price': 150.0,
                    'percent_change': 2.5,
                    'rsi': 65.0,
                    'volume_ratio': 1.2,
                    'news_summary': 'Apple reports strong quarterly earnings'
                }
            ],
            'losers': [
                {
                    'symbol': 'TSLA',
                    'company_name': 'Tesla Inc.',
                    'current_price': 200.0,
                    'percent_change': -1.5,
                    'rsi': 45.0,
                    'volume_ratio': 0.8
                }
            ],
            'collection_success': True
        }
        
        logger.info("Testing script generation with mock data...")
        script_data = script_generator.generate_script(mock_market_data)
        
        if not script_data.get('generation_success'):
            logger.error(f"Script generation failed: {script_data.get('error', 'Unknown error')}")
            return False
        
        logger.info("Script generation completed successfully!")
        
        # Log results
        logger.info(f"Script Generation Results:")
        logger.info(f"  Lead host: {script_data.get('lead_host', 'Unknown')}")
        logger.info(f"  Segments: {len(script_data.get('segments', []))}")
        logger.info(f"  Estimated runtime: {script_data.get('estimated_runtime_minutes', 0)} minutes")
        
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
            for issue in quality_validation['issues'][:3]:  # Show first 3
                logger.warning(f"    - {issue}")
        
        if quality_validation.get('warnings'):
            logger.warning(f"  Warnings: {len(quality_validation['warnings'])}")
            for warning in quality_validation['warnings'][:3]:  # Show first 3
                logger.warning(f"    - {warning}")
        
        if quality_validation.get('passed_checks'):
            logger.info(f"  Passed checks: {len(quality_validation['passed_checks'])}")
            for check in quality_validation['passed_checks'][:3]:  # Show first 3
                logger.info(f"    ✓ {check}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in simple validation test: {str(e)}")
        return False


def main():
    """Run all enhanced system tests"""
    logger.info("Starting Enhanced Market Voices System Test")
    logger.info(f"Test timestamp: {datetime.now().isoformat()}")
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
    
    # Check if we should run simple tests only
    simple_test = os.getenv("SIMPLE_TEST") == "1"
    
    if simple_test:
        logger.info("Running SIMPLE_TEST mode - no API calls")
        tests = [
            ("Simple Validation (Mock Data)", test_simple_validation),
            ("Quality Validation", test_quality_validation)
        ]
    else:
        # Run tests
        tests = [
            ("Enhanced Data Collection", test_enhanced_data_collection),
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
            logger.error(f"Test {test_name} crashed: {str(e)}")
            results[test_name] = "CRASHED"
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status_icon = "✓" if result == "PASSED" else "✗"
        logger.info(f"{status_icon} {test_name}: {result}")
    
    passed_count = sum(1 for result in results.values() if result == "PASSED")
    total_count = len(results)
    
    logger.info(f"\nOverall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        logger.info("🎉 All tests passed! Enhanced system is working correctly.")
    else:
        logger.warning("⚠️  Some tests failed. Please review the issues above.")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 