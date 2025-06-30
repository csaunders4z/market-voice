#!/usr/bin/env python3
"""
Test Two-Phase Workflow for Market Voices
Tests the new two-phase data collection workflow:
Phase 1: Screen all symbols to identify top movers
Phase 2: Deep analysis only for identified top movers
"""
import os
import sys
import json
from datetime import datetime
from loguru import logger

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import modules
from src.data_collection.two_phase_collector import two_phase_collector
from src.data_collection.screening_module import screening_module
from src.data_collection.deep_analysis_module import deep_analysis_module
from src.script_generation.script_generator import script_generator
from src.content_validation.quality_controls import QualityController


def test_two_phase_workflow():
    """Test the complete two-phase workflow"""
    logger.info("=" * 80)
    logger.info("TESTING TWO-PHASE WORKFLOW")
    logger.info("=" * 80)
    
    try:
        # Test Phase 1: Screening
        logger.info("\n📊 PHASE 1: SYMBOL SCREENING")
        logger.info("-" * 50)
        
        # Test with a subset of symbols for faster testing
        screening_result = screening_module.screen_symbols(max_symbols=50)
        
        if not screening_result.get('screening_success'):
            logger.error(f"❌ Screening failed: {screening_result.get('error', 'Unknown error')}")
            return False
        
        # Log screening results
        winners = screening_result.get('winners', [])
        losers = screening_result.get('losers', [])
        total_screened = screening_result.get('total_screened', 0)
        data_source = screening_result.get('data_source', 'Unknown')
        
        logger.info(f"✅ Screening completed successfully!")
        logger.info(f"   Data source: {data_source}")
        logger.info(f"   Total symbols screened: {total_screened}")
        logger.info(f"   Top winners identified: {len(winners)}")
        logger.info(f"   Top losers identified: {len(losers)}")
        
        if winners:
            logger.info(f"   Top winners: {[w.get('symbol') for w in winners]}")
        if losers:
            logger.info(f"   Top losers: {[l.get('symbol') for l in losers]}")
        
        # Test Phase 2: Deep Analysis
        logger.info("\n🔍 PHASE 2: DEEP ANALYSIS")
        logger.info("-" * 50)
        
        if not winners and not losers:
            logger.warning("⚠️  No top movers identified, skipping deep analysis")
            return False
        
        analysis_result = deep_analysis_module.analyze_top_movers(winners, losers)
        
        if not analysis_result.get('analysis_success'):
            logger.error("❌ Deep analysis failed")
            return False
        
        # Log analysis results
        analyzed_winners = analysis_result.get('analyzed_winners', [])
        analyzed_losers = analysis_result.get('analyzed_losers', [])
        total_analyzed = analysis_result.get('total_analyzed', 0)
        
        logger.info(f"✅ Deep analysis completed successfully!")
        logger.info(f"   Total stocks analyzed: {total_analyzed}")
        logger.info(f"   Winners with deep data: {len(analyzed_winners)}")
        logger.info(f"   Losers with deep data: {len(analyzed_losers)}")
        
        # Show sample deep analysis data
        if analyzed_winners:
            sample_winner = analyzed_winners[0]
            logger.info(f"\n📈 Sample Winner Analysis ({sample_winner.get('symbol')}):")
            logger.info(f"   Price: ${sample_winner.get('current_price')} ({sample_winner.get('percent_change', 0):.2f}%)")
            logger.info(f"   Volume: {sample_winner.get('volume_ratio', 1.0):.1f}x average")
            
            if sample_winner.get('earnings_data'):
                logger.info(f"   Earnings: {sample_winner['earnings_data'].get('date', 'N/A')}")
            
            if sample_winner.get('analyst_data'):
                consensus = sample_winner['analyst_data'].get('consensus', 'hold')
                logger.info(f"   Analyst Consensus: {consensus.upper()}")
            
            if sample_winner.get('technical_data'):
                rsi = sample_winner['technical_data'].get('rsi', 50)
                signals = sample_winner['technical_data'].get('technical_signals', [])
                logger.info(f"   RSI: {rsi}")
                if signals:
                    logger.info(f"   Technical Signals: {', '.join(signals)}")
        
        # Test Complete Two-Phase Workflow
        logger.info("\n🔄 COMPLETE TWO-PHASE WORKFLOW")
        logger.info("-" * 50)
        
        complete_result = two_phase_collector.collect_data(max_symbols=50)
        
        if not complete_result.get('collection_success'):
            logger.error(f"❌ Complete workflow failed: {complete_result.get('error', 'Unknown error')}")
            return False
        
        # Log complete workflow results
        workflow_phases = complete_result.get('workflow_phases', {})
        market_summary = complete_result.get('market_summary', {})
        final_winners = complete_result.get('winners', [])
        final_losers = complete_result.get('losers', [])
        
        logger.info(f"✅ Complete two-phase workflow successful!")
        logger.info(f"   Workflow type: {market_summary.get('workflow_type', 'Unknown')}")
        logger.info(f"   Market sentiment: {market_summary.get('market_sentiment', 'Unknown')}")
        logger.info(f"   Final winners: {len(final_winners)}")
        logger.info(f"   Final losers: {len(final_losers)}")
        logger.info(f"   Average change: {market_summary.get('average_change', 0):.2f}%")
        
        # Test Script Generation with Two-Phase Data
        logger.info("\n📝 SCRIPT GENERATION WITH TWO-PHASE DATA")
        logger.info("-" * 50)
        
        script_data = script_generator.generate_script(complete_result)
        
        if not script_data.get('generation_success'):
            logger.error(f"❌ Script generation failed: {script_data.get('error', 'Unknown error')}")
            return False
        
        # Log script generation results
        logger.info(f"✅ Script generation successful!")
        logger.info(f"   Lead host: {script_data.get('lead_host', 'Unknown')}")
        logger.info(f"   Segments: {len(script_data.get('segments', []))}")
        logger.info(f"   Estimated runtime: {script_data.get('estimated_runtime_minutes', 0)} minutes")
        
        # Check quality metrics
        quality_metrics = script_data.get('quality_metrics', {})
        logger.info(f"   Total words: {quality_metrics.get('total_words', 0)}")
        logger.info(f"   Technical indicators used: {quality_metrics.get('technical_indicators_used', 0)}")
        logger.info(f"   News sources referenced: {quality_metrics.get('news_sources_referenced', 0)}")
        
        # Test Quality Validation
        logger.info("\n🔍 QUALITY VALIDATION")
        logger.info("-" * 50)
        
        quality_controller = QualityController()
        quality_results = quality_controller.validate_script_quality(script_data)
        
        overall_score = quality_results.get('overall_score', 0)
        logger.info(f"✅ Quality validation completed!")
        logger.info(f"   Overall score: {overall_score:.1f}%")
        
        if quality_results.get('issues'):
            logger.warning(f"   Issues found: {len(quality_results['issues'])}")
            for issue in quality_results['issues'][:3]:  # Show first 3
                logger.warning(f"     - {issue}")
        
        if quality_results.get('passed_checks'):
            logger.info(f"   Passed checks: {len(quality_results['passed_checks'])}")
            for check in quality_results['passed_checks'][:3]:  # Show first 3
                logger.info(f"     ✓ {check}")
        
        # Save test results
        logger.info("\n💾 SAVING TEST RESULTS")
        logger.info("-" * 50)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save complete workflow data
        data_file = f"output/two_phase_workflow_data_{timestamp}.json"
        os.makedirs("output", exist_ok=True)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(complete_result, f, indent=2, default=str)
        
        # Save script
        script_file = f"output/two_phase_script_{timestamp}.txt"
        formatted_script = script_generator.format_script_for_output(script_data)
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(formatted_script)
        
        logger.info(f"✅ Test results saved:")
        logger.info(f"   Data: {data_file}")
        logger.info(f"   Script: {script_file}")
        
        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("🎉 TWO-PHASE WORKFLOW TEST COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        logger.info(f"   Screening: {total_screened} symbols → {len(winners + losers)} top movers")
        logger.info(f"   Deep Analysis: {total_analyzed} stocks with detailed data")
        logger.info(f"   Script Quality: {overall_score:.1f}%")
        logger.info(f"   Data Source: {data_source}")
        logger.info(f"   Workflow Type: Two-Phase Collection")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Two-phase workflow test failed: {str(e)}")
        return False


def test_individual_phases():
    """Test individual phases separately"""
    logger.info("\n🧪 TESTING INDIVIDUAL PHASES")
    logger.info("=" * 50)
    
    # Test screening module
    logger.info("\n📊 Testing Screening Module")
    screening_result = screening_module.screen_symbols(max_symbols=25)
    if screening_result.get('screening_success'):
        logger.info(f"✅ Screening test passed: {screening_result.get('total_screened', 0)} symbols")
    else:
        logger.error(f"❌ Screening test failed: {screening_result.get('error')}")
        return False
    
    # Test deep analysis module
    logger.info("\n🔍 Testing Deep Analysis Module")
    winners = screening_result.get('winners', [])[:2]  # Test with 2 winners
    losers = screening_result.get('losers', [])[:2]    # Test with 2 losers
    
    if winners or losers:
        analysis_result = deep_analysis_module.analyze_top_movers(winners, losers)
        if analysis_result.get('analysis_success'):
            logger.info(f"✅ Deep analysis test passed: {analysis_result.get('total_analyzed', 0)} stocks")
        else:
            logger.error("❌ Deep analysis test failed")
            return False
    else:
        logger.warning("⚠️  Skipping deep analysis test - no movers identified")
    
    return True


def main():
    """Run the two-phase workflow tests"""
    logger.info("Starting Two-Phase Workflow Tests")
    logger.info(f"Test timestamp: {datetime.now().isoformat()}")
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
    
    # Test individual phases first
    individual_ok = test_individual_phases()
    
    if individual_ok:
        # Test complete workflow
        complete_ok = test_two_phase_workflow()
        
        if complete_ok:
            logger.info("\n🎉 ALL TWO-PHASE WORKFLOW TESTS PASSED!")
            logger.info("✅ Individual phases working correctly")
            logger.info("✅ Complete workflow functioning properly")
            logger.info("✅ Two-phase implementation successful")
        else:
            logger.error("\n❌ Complete workflow test failed!")
            return False
    else:
        logger.error("\n❌ Individual phase tests failed!")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    print(f"\nTwo-phase workflow test completed with {'SUCCESS' if success else 'FAILURE'}")
    sys.exit(0 if success else 1) 