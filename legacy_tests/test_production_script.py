#!/usr/bin/env python3
"""
Production Script Test for Market Voices
Tests actual script generation with expanded symbol coverage
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
from src.script_generation.script_generator import ScriptGenerator
from src.content_validation.quality_controls import QualityController


def test_production_script_generation():
    """Test actual script generation with production data"""
    logger.info("=" * 80)
    logger.info("PRODUCTION SCRIPT GENERATION TEST")
    logger.info("=" * 80)
    
    try:
        # Initialize components
        unified_collector = UnifiedDataCollector()
        script_generator = ScriptGenerator()
        quality_controller = QualityController()
        
        # Use a reasonable subset for production testing
        test_symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX",
            "ADBE", "CRM", "PYPL", "INTC", "AMD", "QCOM", "AVGO", "TXN",
            "COST", "PEP", "CSCO", "TMUS", "JNJ", "PG", "UNH", "HD", "JPM"
        ]
        
        logger.info(f"Collecting production data for {len(test_symbols)} symbols...")
        
        # Collect data (not in test mode)
        market_data = unified_collector.collect_data(symbols=test_symbols, production_mode=True)
        
        if not market_data.get('collection_success'):
            logger.error(f"Data collection failed: {market_data.get('error', 'Unknown error')}")
            return False
        
        # Analyze collected data
        summary = market_data.get('market_summary', {})
        all_data = market_data.get('all_data', [])
        winners = market_data.get('winners', [])
        losers = market_data.get('losers', [])
        
        logger.info(f"\nProduction Data Results:")
        logger.info(f"  Total stocks: {len(all_data)}")
        logger.info(f"  Advancing: {summary.get('advancing_stocks', 0)}")
        logger.info(f"  Declining: {summary.get('declining_stocks', 0)}")
        logger.info(f"  Average change: {summary.get('average_change', 0):.2f}%")
        logger.info(f"  Market sentiment: {summary.get('market_sentiment', 'Unknown')}")
        logger.info(f"  Data source: {summary.get('data_source', 'Unknown')}")
        
        # Show top movers
        logger.info(f"\nTop 5 Winners:")
        for i, winner in enumerate(winners[:5], 1):
            logger.info(f"  {i}. {winner.get('symbol')}: +{winner.get('percent_change', 0):.2f}% (Volume: {winner.get('volume_ratio', 1):.1f}x)")
        
        logger.info(f"\nTop 5 Losers:")
        for i, loser in enumerate(losers[:5], 1):
            logger.info(f"  {i}. {loser.get('symbol')}: {loser.get('percent_change', 0):.2f}% (Volume: {loser.get('volume_ratio', 1):.1f}x)")
        
        # Generate actual script (not mock)
        logger.info(f"\nGenerating production script...")
        
        # Temporarily disable test mode for script generation
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "0"
        
        try:
            script_data = script_generator.generate_script(market_data)
        finally:
            # Restore test mode
            if original_test_mode:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
        
        if not script_data.get('generation_success'):
            logger.error(f"Script generation failed: {script_data.get('error', 'Unknown error')}")
            return False
        
        # Analyze script results
        logger.info(f"\nProduction Script Results:")
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
        
        # Show sample content
        if winner_segments:
            logger.info(f"\nSample Winner Segment:")
            sample_segment = winner_segments[0]
            logger.info(f"  Stock: {sample_segment.get('stock', 'Unknown')}")
            logger.info(f"  Host: {sample_segment.get('host', 'Unknown')}")
            logger.info(f"  Text preview: {sample_segment.get('text', '')[:200]}...")
        
        if loser_segments:
            logger.info(f"\nSample Loser Segment:")
            sample_segment = loser_segments[0]
            logger.info(f"  Stock: {sample_segment.get('stock', 'Unknown')}")
            logger.info(f"  Host: {sample_segment.get('host', 'Unknown')}")
            logger.info(f"  Text preview: {sample_segment.get('text', '')[:200]}...")
        
        # Format and save script
        formatted_script = script_generator.format_script_for_output(script_data)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_file = f"production_script_{timestamp}.txt"
        
        with open(script_file, 'w') as f:
            f.write(formatted_script)
        
        logger.info(f"\nScript saved to: {script_file}")
        logger.info(f"Script length: {len(formatted_script)} characters")
        
        # Show script preview
        logger.info(f"\nScript Preview (first 500 characters):")
        logger.info("-" * 80)
        logger.info(formatted_script[:500] + "..." if len(formatted_script) > 500 else formatted_script)
        logger.info("-" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in production script generation test: {str(e)}")
        return False


def test_script_quality_analysis():
    """Test detailed script quality analysis"""
    logger.info("\n" + "=" * 80)
    logger.info("SCRIPT QUALITY ANALYSIS")
    logger.info("=" * 80)
    
    try:
        quality_controller = QualityController()
        
        # Create a comprehensive test script with expanded coverage
        test_script = {
            "intro": "Welcome to Market Voices! I'm Marcus, and today we're breaking down the expanded NASDAQ-100 and S&P 500 performance with my colleague Suzanne. We've analyzed over 200 stocks today, giving us unprecedented breadth and depth in our market coverage.",
            "market_overview": "Today's session showed remarkable breadth across the expanded universe of stocks we're now covering. With our enhanced data collection covering both NASDAQ-100 and S&P 500 constituents, we're seeing sector rotation patterns that weren't visible with our previous limited scope. The market is showing resilience despite some volatility, with institutional investors positioning for continued economic growth.",
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
                },
                {
                    "host": "marcus",
                    "stock": "GOOGL",
                    "text": "Alphabet Inc. rallied 2.2% today, outperforming its tech peers. The move was driven by strong advertising revenue growth and positive analyst sentiment. The company's cloud division continues to gain market share, while its AI initiatives are showing promising results. Technical indicators show the stock above key resistance levels with healthy volume. This reflects the broader market's confidence in Alphabet's ability to compete in the AI space."
                },
                {
                    "host": "suzanne",
                    "stock": "AMZN",
                    "text": "Amazon.com Inc. advanced 1.9% today, building on recent momentum. The catalyst was strong e-commerce sales data and positive analyst commentary on the company's AWS cloud business. The technical setup shows the stock in a bullish trend with RSI at 68, indicating strong momentum. Volume was 1.8 times the average, suggesting institutional buying. This move reflects confidence in Amazon's diversified business model and market leadership."
                },
                {
                    "host": "marcus",
                    "stock": "NVDA",
                    "text": "NVIDIA Corporation gained 3.1% today, leading the semiconductor sector higher. The catalyst was strong demand for AI chips and positive analyst upgrades. The company's data center business continues to show exceptional growth, driven by AI and machine learning applications. Technical analysis shows the stock breaking out to new highs with massive volume. This reflects the market's recognition of NVIDIA's dominant position in the AI chip market."
                }
            ],
            "loser_segments": [
                {
                    "host": "suzanne",
                    "stock": "TSLA",
                    "text": "Tesla Inc. declined 1.2% today, underperforming the broader market. The drop was primarily driven by regulatory concerns as the NHTSA expanded its investigation into Autopilot safety. Additionally, competition in the EV space is intensifying, with traditional automakers launching competitive models. Technical indicators show the stock testing support levels with RSI at 35, indicating oversold conditions. However, volume was below average, suggesting limited selling pressure."
                },
                {
                    "host": "marcus",
                    "stock": "NFLX",
                    "text": "Netflix Inc. fell 0.8% today, continuing its recent weakness. The decline was driven by concerns about subscriber growth and increasing competition in the streaming space. The company's recent earnings report showed mixed results, with international growth offsetting domestic challenges. Technical analysis shows the stock below key moving averages with declining volume. Analysts remain cautious about the company's ability to maintain its market leadership position."
                },
                {
                    "host": "suzanne",
                    "stock": "PYPL",
                    "text": "PayPal Holdings Inc. dropped 1.5% today, underperforming the fintech sector. The decline was driven by concerns about competition from Apple Pay and other digital payment solutions. The company's recent earnings showed slower growth than expected, raising questions about its market position. Technical indicators show the stock in a downtrend with RSI at 28, indicating oversold conditions. Volume was elevated, suggesting institutional selling."
                },
                {
                    "host": "marcus",
                    "stock": "INTC",
                    "text": "Intel Corporation declined 0.9% today, lagging behind its semiconductor peers. The drop was driven by concerns about market share loss to AMD and other competitors. The company's recent product launches have been met with mixed reviews, raising questions about its competitive position. Technical analysis shows the stock below key support levels with declining volume. Analysts are cautious about Intel's ability to regain market leadership."
                },
                {
                    "host": "suzanne",
                    "stock": "CRM",
                    "text": "Salesforce Inc. fell 1.1% today, underperforming the software sector. The decline was driven by concerns about slowing growth and increased competition in the CRM space. The company's recent earnings showed solid results but guidance was below expectations. Technical indicators show the stock testing support levels with RSI at 42. Volume was below average, suggesting limited selling pressure. Analysts remain positive on the company's long-term prospects."
                }
            ],
            "market_sentiment": "Overall market sentiment remains positive despite some volatility. The expanded coverage reveals sector rotation patterns that suggest institutional investors are positioning for continued economic growth while managing risk through diversification. Technology stocks continue to lead the market higher, while defensive sectors show relative weakness. This reflects confidence in the economic recovery and corporate earnings growth.",
            "outro": "This concludes today's Market Voices analysis. Thanks for joining us as we continue to provide comprehensive coverage of the expanded NASDAQ-100 and S&P 500 universe. Our enhanced data collection and analysis gives us unprecedented insights into market movements. This is Marcus, signing off."
        }
        
        # Run comprehensive quality validation
        validation_results = quality_controller.validate_script_quality(test_script)
        
        logger.info(f"Comprehensive Quality Analysis:")
        logger.info(f"  Overall score: {validation_results.get('overall_score', 0):.1f}%")
        logger.info(f"  Passed checks: {len(validation_results.get('passed_checks', []))}")
        logger.info(f"  Issues found: {len(validation_results.get('issues', []))}")
        logger.info(f"  Warnings: {len(validation_results.get('warnings', []))}")
        
        if validation_results.get('passed_checks'):
            logger.info(f"\nPassed Checks:")
            for check in validation_results['passed_checks']:
                logger.info(f"  ✓ {check}")
        
        if validation_results.get('issues'):
            logger.warning(f"\nIssues Found:")
            for issue in validation_results['issues']:
                logger.warning(f"  - {issue}")
        
        if validation_results.get('warnings'):
            logger.warning(f"\nWarnings:")
            for warning in validation_results['warnings']:
                logger.warning(f"  - {warning}")
        
        # Calculate word count
        total_text = ""
        for segment in test_script.get('winner_segments', []):
            total_text += segment.get('text', '') + " "
        for segment in test_script.get('loser_segments', []):
            total_text += segment.get('text', '') + " "
        total_text += test_script.get('intro', '') + " "
        total_text += test_script.get('market_overview', '') + " "
        total_text += test_script.get('market_sentiment', '') + " "
        total_text += test_script.get('outro', '')
        
        word_count = len(total_text.split())
        logger.info(f"\nContent Analysis:")
        logger.info(f"  Total words: {word_count}")
        logger.info(f"  Winner segments: {len(test_script.get('winner_segments', []))}")
        logger.info(f"  Loser segments: {len(test_script.get('loser_segments', []))}")
        logger.info(f"  Average segment length: {word_count // (len(test_script.get('winner_segments', [])) + len(test_script.get('loser_segments', [])))} words")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in script quality analysis: {str(e)}")
        return False


def main():
    """Run production tests"""
    logger.info("Starting Production Script Tests")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    tests = [
        ("Production Script Generation", test_production_script_generation),
        ("Script Quality Analysis", test_script_quality_analysis)
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
    logger.info("PRODUCTION TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result == "PASSED" else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    passed_count = sum(1 for result in results.values() if result == "PASSED")
    total_count = len(results)
    
    logger.info(f"\nOverall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        logger.info("🎉 All production tests passed! System is ready for expanded coverage.")
    else:
        logger.warning("⚠️  Some production tests failed. Please review the logs above.")
    
    return passed_count == total_count


if __name__ == "__main__":
    main() 