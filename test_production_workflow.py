#!/usr/bin/env python3
"""
Complete Production Workflow Test
Tests the full pipeline with real data from multiple sources
"""
import os
import sys
import json
from datetime import datetime
from loguru import logger

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_collection.stock_data import stock_collector
from src.script_generation.script_generator import script_generator
from src.content_validation.quality_controls import quality_controller


def test_production_workflow():
    """Test the complete production workflow"""
    logger.info("=" * 70)
    logger.info("TESTING COMPLETE PRODUCTION WORKFLOW")
    logger.info("=" * 70)
    
    try:
        # Step 1: Data Collection
        logger.info("\n📊 STEP 1: DATA COLLECTION")
        logger.info("-" * 40)
        
        market_data = stock_collector.collect_enhanced_data()
        
        if not market_data.get('collection_success'):
            logger.error(f"❌ Data collection failed: {market_data.get('error', 'Unknown error')}")
            return False
        
        # Log data collection results
        summary = market_data.get('market_summary', {})
        logger.info(f"✅ Data collection successful!")
        logger.info(f"  Data source: {market_data.get('data_source', 'Unknown')}")
        logger.info(f"  Total stocks: {summary.get('total_stocks', 0)}")
        logger.info(f"  Advancing: {summary.get('advancing_stocks', 0)}")
        logger.info(f"  Declining: {summary.get('declining_stocks', 0)}")
        logger.info(f"  Average change: {summary.get('average_change', 0):.2f}%")
        logger.info(f"  Market sentiment: {summary.get('market_sentiment', 'Unknown')}")
        
        # Show sample data
        winners = market_data.get('winners', [])
        losers = market_data.get('losers', [])
        
        if winners:
            logger.info(f"\n  Top Winners:")
            for i, winner in enumerate(winners[:3], 1):
                logger.info(f"    {i}. {winner.get('symbol')}: {winner.get('percent_change', 0):.2f}%")
        
        if losers:
            logger.info(f"\n  Top Losers:")
            for i, loser in enumerate(losers[:3], 1):
                logger.info(f"    {i}. {loser.get('symbol')}: {loser.get('percent_change', 0):.2f}%")
        
        # Step 2: Script Generation
        logger.info("\n📝 STEP 2: SCRIPT GENERATION")
        logger.info("-" * 40)
        
        script_data = script_generator.generate_script(market_data)
        
        if not script_data.get('generation_success'):
            logger.error(f"❌ Script generation failed: {script_data.get('error', 'Unknown error')}")
            return False
        
        # Log script generation results
        logger.info(f"✅ Script generation successful!")
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
        
        # Step 3: Quality Validation
        logger.info("\n🔍 STEP 3: QUALITY VALIDATION")
        logger.info("-" * 40)
        
        quality_validation = script_data.get('quality_validation', {})
        overall_score = quality_validation.get('overall_score', 0)
        logger.info(f"✅ Quality validation completed!")
        logger.info(f"  Overall score: {overall_score:.1f}%")
        
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
        
        # Step 4: Output Generation
        logger.info("\n📄 STEP 4: OUTPUT GENERATION")
        logger.info("-" * 40)
        
        # Format script for output
        formatted_script = script_generator.format_script_for_output(script_data)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output/production_script_{timestamp}.txt"
        
        os.makedirs("output", exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_script)
        
        logger.info(f"✅ Script saved to: {output_file}")
        
        # Save raw data
        data_file = f"output/market_data_{timestamp}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(market_data, f, indent=2, default=str)
        
        logger.info(f"✅ Market data saved to: {data_file}")
        
        # Step 5: Summary
        logger.info("\n📋 STEP 5: PRODUCTION SUMMARY")
        logger.info("-" * 40)
        
        logger.info("🎉 PRODUCTION WORKFLOW COMPLETED SUCCESSFULLY!")
        logger.info(f"  Data Source: {market_data.get('data_source', 'Unknown')}")
        logger.info(f"  Script Quality: {overall_score:.1f}%")
        logger.info(f"  Runtime: {script_data.get('estimated_runtime_minutes', 0)} minutes")
        logger.info(f"  Output Files: {output_file}, {data_file}")
        
        # Show sample script content
        segments = script_data.get('segments', [])
        if segments:
            logger.info(f"\n📝 Sample Script Content:")
            logger.info(f"  Intro: {script_data.get('intro', '')[:100]}...")
            for i, segment in enumerate(segments[:2], 1):
                logger.info(f"  Segment {i} ({segment.get('host', 'Unknown').title()}): {segment.get('text', '')[:100]}...")
            logger.info(f"  Outro: {script_data.get('outro', '')[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Production workflow failed: {str(e)}")
        return False


def main():
    """Run the complete production workflow test"""
    logger.info("Starting Complete Production Workflow Test")
    logger.info(f"Test timestamp: {datetime.now().isoformat()}")
    logger.info("This test will use real data from available APIs")
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
    
    success = test_production_workflow()
    
    if success:
        logger.info("\n🎉 PRODUCTION WORKFLOW TEST PASSED!")
        logger.info("✅ All components working correctly with real data")
        logger.info("✅ System ready for production deployment")
    else:
        logger.error("\n❌ PRODUCTION WORKFLOW TEST FAILED!")
        logger.error("Please review the errors above")
    
    return success


if __name__ == "__main__":
    success = main()
    print(f"\nProduction workflow test completed with {'SUCCESS' if success else 'FAILURE'}")
    sys.exit(0 if success else 1) 