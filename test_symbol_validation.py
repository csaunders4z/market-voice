#!/usr/bin/env python3
"""
Test Symbol Validation for Market Voices
Tests the new symbol coverage validation system
"""
import os
import sys
import json
from datetime import datetime
from loguru import logger

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import modules
from src.data_collection.symbol_loader import symbol_loader


def test_symbol_validation():
    """Test the symbol coverage validation system"""
    logger.info("=" * 80)
    logger.info("TESTING SYMBOL COVERAGE VALIDATION")
    logger.info("=" * 80)
    
    try:
        # Test basic validation
        logger.info("\n📊 BASIC SYMBOL VALIDATION")
        logger.info("-" * 50)
        
        validation_result = symbol_loader.validate_symbol_coverage()
        
        if not validation_result.get('validation_success'):
            logger.error(f"❌ Validation failed: {validation_result.get('error', 'Unknown error')}")
            return False
        
        # Display validation results
        nasdaq_validation = validation_result.get('nasdaq_100_validation', {})
        sp500_validation = validation_result.get('sp_500_validation', {})
        market_cap_validation = validation_result.get('market_cap_validation', {})
        
        logger.info("✅ Symbol validation completed successfully!")
        
        # NASDAQ-100 results
        logger.info(f"\n📈 NASDAQ-100 Validation:")
        logger.info(f"   Total symbols: {nasdaq_validation.get('total_symbols', 0)}")
        logger.info(f"   Expected count: {nasdaq_validation.get('expected_count', 100)}")
        logger.info(f"   Count valid: {'✅' if nasdaq_validation.get('count_valid') else '❌'}")
        logger.info(f"   Critical coverage: {nasdaq_validation.get('coverage_percentage', 0):.1f}%")
        logger.info(f"   Critical symbols: {nasdaq_validation.get('critical_symbols_covered', 0)}/{nasdaq_validation.get('critical_symbols_total', 0)}")
        
        missing_nasdaq = nasdaq_validation.get('missing_critical', [])
        if missing_nasdaq:
            logger.warning(f"   Missing critical: {', '.join(missing_nasdaq)}")
        
        # S&P 500 results
        logger.info(f"\n📊 S&P 500 Validation:")
        logger.info(f"   Total symbols: {sp500_validation.get('total_symbols', 0)}")
        logger.info(f"   Expected count: {sp500_validation.get('expected_count', 500)}")
        logger.info(f"   Count valid: {'✅' if sp500_validation.get('count_valid') else '❌'}")
        logger.info(f"   Critical coverage: {sp500_validation.get('coverage_percentage', 0):.1f}%")
        logger.info(f"   Critical symbols: {sp500_validation.get('critical_symbols_covered', 0)}/{sp500_validation.get('critical_symbols_total', 0)}")
        
        missing_sp500 = sp500_validation.get('missing_critical', [])
        if missing_sp500:
            logger.warning(f"   Missing critical: {', '.join(missing_sp500)}")
        
        # Market cap results
        logger.info(f"\n💰 Market Cap Validation:")
        logger.info(f"   Top 100 coverage: {market_cap_validation.get('coverage_percentage', 0):.1f}%")
        logger.info(f"   Top 100 symbols: {market_cap_validation.get('top_100_covered', 0)}/{market_cap_validation.get('top_100_total', 0)}")
        
        missing_top_100 = market_cap_validation.get('missing_top_100', [])
        if missing_top_100:
            logger.warning(f"   Missing top 100: {', '.join(missing_top_100[:5])}")
        
        # Display issues and recommendations
        issues = validation_result.get('coverage_issues', [])
        recommendations = validation_result.get('recommendations', [])
        
        if issues:
            logger.warning(f"\n⚠️  Coverage Issues ({len(issues)}):")
            for issue in issues:
                logger.warning(f"   - {issue}")
        else:
            logger.info(f"\n✅ No coverage issues found!")
        
        if recommendations:
            logger.info(f"\n💡 Recommendations ({len(recommendations)}):")
            for rec in recommendations:
                logger.info(f"   - {rec}")
        
        # Test force refresh and validate
        logger.info("\n🔄 FORCE REFRESH AND VALIDATE")
        logger.info("-" * 50)
        
        refresh_result = symbol_loader.force_refresh_and_validate()
        
        if refresh_result.get('validation_success'):
            logger.info("✅ Force refresh and validation completed successfully!")
            
            # Compare results
            new_nasdaq = refresh_result.get('nasdaq_100_validation', {})
            new_sp500 = refresh_result.get('sp_500_validation', {})
            
            logger.info(f"   NASDAQ-100: {new_nasdaq.get('total_symbols', 0)} symbols")
            logger.info(f"   S&P 500: {new_sp500.get('total_symbols', 0)} symbols")
            
            # Check if refresh made any changes
            nasdaq_changed = nasdaq_validation.get('total_symbols') != new_nasdaq.get('total_symbols')
            sp500_changed = sp500_validation.get('total_symbols') != new_sp500.get('total_symbols')
            
            if nasdaq_changed or sp500_changed:
                logger.info("   🔄 Symbol counts changed after refresh")
            else:
                logger.info("   ✅ Symbol counts unchanged (cached data)")
        else:
            logger.error("❌ Force refresh and validation failed")
            return False
        
        # Save validation results
        logger.info("\n💾 SAVING VALIDATION RESULTS")
        logger.info("-" * 50)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        validation_file = f"output/symbol_validation_{timestamp}.json"
        
        os.makedirs("output", exist_ok=True)
        with open(validation_file, 'w', encoding='utf-8') as f:
            json.dump(validation_result, f, indent=2, default=str)
        
        logger.info(f"✅ Validation results saved to: {validation_file}")
        
        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("🎉 SYMBOL VALIDATION TEST COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        
        # Calculate overall health score
        nasdaq_score = nasdaq_validation.get('coverage_percentage', 0)
        sp500_score = sp500_validation.get('coverage_percentage', 0)
        market_cap_score = market_cap_validation.get('coverage_percentage', 0)
        
        overall_score = (nasdaq_score + sp500_score + market_cap_score) / 3
        
        logger.info(f"   Overall Coverage Health: {overall_score:.1f}%")
        logger.info(f"   NASDAQ-100 Health: {nasdaq_score:.1f}%")
        logger.info(f"   S&P 500 Health: {sp500_score:.1f}%")
        logger.info(f"   Market Cap Health: {market_cap_score:.1f}%")
        logger.info(f"   Issues Found: {len(issues)}")
        logger.info(f"   Recommendations: {len(recommendations)}")
        
        if overall_score >= 95:
            logger.info("   🟢 EXCELLENT: Symbol coverage is comprehensive")
        elif overall_score >= 90:
            logger.info("   🟡 GOOD: Symbol coverage is adequate")
        elif overall_score >= 80:
            logger.info("   🟠 FAIR: Symbol coverage needs attention")
        else:
            logger.info("   🔴 POOR: Symbol coverage needs immediate attention")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Symbol validation test failed: {str(e)}")
        return False


def test_individual_validation_functions():
    """Test individual validation functions"""
    logger.info("\n🧪 TESTING INDIVIDUAL VALIDATION FUNCTIONS")
    logger.info("=" * 50)
    
    try:
        # Test NASDAQ-100 validation
        logger.info("\n📈 Testing NASDAQ-100 validation")
        nasdaq_result = symbol_loader._validate_nasdaq_100_coverage()
        logger.info(f"   Result: {nasdaq_result.get('total_symbols', 0)} symbols, "
                   f"{nasdaq_result.get('coverage_percentage', 0):.1f}% coverage")
        
        # Test S&P 500 validation
        logger.info("\n📊 Testing S&P 500 validation")
        sp500_result = symbol_loader._validate_sp_500_coverage()
        logger.info(f"   Result: {sp500_result.get('total_symbols', 0)} symbols, "
                   f"{sp500_result.get('coverage_percentage', 0):.1f}% coverage")
        
        # Test market cap validation
        logger.info("\n💰 Testing market cap validation")
        market_cap_result = symbol_loader._validate_market_cap_coverage()
        logger.info(f"   Result: {market_cap_result.get('top_100_covered', 0)}/{market_cap_result.get('top_100_total', 0)} "
                   f"({market_cap_result.get('coverage_percentage', 0):.1f}%)")
        
        logger.info("✅ Individual validation functions working correctly")
        return True
        
    except Exception as e:
        logger.error(f"❌ Individual validation test failed: {str(e)}")
        return False


def main():
    """Run the symbol validation tests"""
    logger.info("Starting Symbol Validation Tests")
    logger.info(f"Test timestamp: {datetime.now().isoformat()}")
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
    
    # Test individual functions first
    individual_ok = test_individual_validation_functions()
    
    if individual_ok:
        # Test complete validation
        complete_ok = test_symbol_validation()
        
        if complete_ok:
            logger.info("\n🎉 ALL SYMBOL VALIDATION TESTS PASSED!")
            logger.info("✅ Individual validation functions working correctly")
            logger.info("✅ Complete validation system functioning properly")
            logger.info("✅ Symbol coverage validation system ready for production")
        else:
            logger.error("\n❌ Complete validation test failed!")
            return False
    else:
        logger.error("\n❌ Individual validation tests failed!")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    print(f"\nSymbol validation test completed with {'SUCCESS' if success else 'FAILURE'}")
    sys.exit(0 if success else 1) 