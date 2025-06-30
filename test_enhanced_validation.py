#!/usr/bin/env python3
"""
Test Enhanced Validation System
Run comprehensive validation on current symbol coverage
"""
import sys
import os
import time
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.content_validation.enhanced_validation import EnhancedValidator
from src.data_collection.symbol_loader import SymbolLoader
from src.utils.logger import get_logger

def test_enhanced_validation():
    """Test the enhanced validation system"""
    print("=" * 80)
    print("ENHANCED VALIDATION SYSTEM TEST")
    print("=" * 80)
    
    # Setup logging
    logger = get_logger()
    
    # Initialize components
    validator = EnhancedValidator()
    symbol_loader = SymbolLoader()
    
    # Get current symbols
    print("\n1. Loading current symbol coverage...")
    all_symbols = symbol_loader.get_all_symbols()
    nasdaq_symbols = symbol_loader.get_nasdaq_100_symbols()
    sp500_symbols = symbol_loader.get_sp_500_symbols()
    
    print(f"   Total symbols: {len(all_symbols)}")
    print(f"   NASDAQ-100 symbols: {len(nasdaq_symbols)}")
    print(f"   S&P 500 symbols: {len(sp500_symbols)}")
    
    # Run comprehensive validation
    print("\n2. Running comprehensive validation...")
    start_time = time.time()
    
    validation_results = validator.run_comprehensive_validation(all_symbols)
    
    end_time = time.time()
    validation_time = end_time - start_time
    
    print(f"   Validation completed in {validation_time:.2f} seconds")
    
    # Display results
    print("\n3. VALIDATION RESULTS")
    print("-" * 50)
    
    # Overall health score
    health_score = validation_results.get('overall_health_score', 0)
    print(f"Overall Health Score: {health_score:.1f}%")
    
    # Sector coverage
    sector_coverage = validation_results.get('sector_coverage', {})
    print(f"\nSector Coverage:")
    print(f"  Coverage: {sector_coverage.get('sector_coverage_percentage', 0):.1f}% ({sector_coverage.get('covered_sectors', 0)}/{sector_coverage.get('total_sectors', 0)} sectors)")
    print(f"  Balance Score: {sector_coverage.get('sector_balance_score', 0):.1f}%")
    
    sector_distribution = sector_coverage.get('sector_distribution', {})
    if sector_distribution:
        print("  Sector Distribution:")
        for sector, count in sorted(sector_distribution.items(), key=lambda x: x[1], reverse=True):
            print(f"    {sector}: {count} symbols")
    
    missing_sectors = sector_coverage.get('missing_sectors', [])
    if missing_sectors:
        print(f"  Missing Sectors: {', '.join(missing_sectors)}")
    
    # Market cap distribution
    market_cap = validation_results.get('market_cap_distribution', {})
    print(f"\nMarket Cap Distribution:")
    print(f"  Balance Score: {market_cap.get('balance_score', 0):.1f}%")
    print(f"  Has Mega Cap: {market_cap.get('has_mega_cap', False)}")
    print(f"  Has Large Cap: {market_cap.get('has_large_cap', False)}")
    print(f"  Has Mid Cap: {market_cap.get('has_mid_cap', False)}")
    
    category_counts = market_cap.get('market_cap_categories', {})
    if category_counts:
        print("  Category Distribution:")
        for category, count in category_counts.items():
            print(f"    {category}: {count} symbols")
    
    # Geographic distribution
    geographic = validation_results.get('geographic_distribution', {})
    print(f"\nGeographic Distribution:")
    print(f"  US Percentage: {geographic.get('us_percentage', 0):.1f}%")
    print(f"  International Percentage: {geographic.get('international_percentage', 0):.1f}%")
    print(f"  Diversity Score: {geographic.get('diversity_score', 0):.1f}%")
    print(f"  Has International: {geographic.get('has_international', False)}")
    
    # Volatility analysis
    volatility = validation_results.get('volatility_analysis', {})
    print(f"\nVolatility Analysis:")
    print(f"  High Volatility: {volatility.get('high_volatility_percentage', 0):.1f}%")
    print(f"  Low Volatility: {volatility.get('low_volatility_percentage', 0):.1f}%")
    print(f"  Average Volatility: {volatility.get('average_volatility', 0):.2f}%")
    print(f"  Volatility Balanced: {volatility.get('volatility_balanced', False)}")
    
    # Liquidity validation
    liquidity = validation_results.get('liquidity_validation', {})
    print(f"\nLiquidity Validation:")
    print(f"  High Liquidity: {liquidity.get('high_liquidity_percentage', 0):.1f}%")
    print(f"  Low Liquidity: {liquidity.get('low_liquidity_percentage', 0):.1f}%")
    print(f"  Average Volume: {liquidity.get('average_volume', 0):,.0f}")
    print(f"  Liquidity Adequate: {liquidity.get('liquidity_adequate', False)}")
    
    # News coverage
    news_coverage = validation_results.get('news_coverage', {})
    print(f"\nNews Coverage:")
    print(f"  Well Covered: {news_coverage.get('well_covered_percentage', 0):.1f}%")
    print(f"  Poorly Covered: {news_coverage.get('poorly_covered_percentage', 0):.1f}%")
    print(f"  Average Coverage Score: {news_coverage.get('average_coverage_score', 0):.1f}")
    print(f"  Coverage Adequate: {news_coverage.get('coverage_adequate', False)}")
    
    # Recommendations
    recommendations = validation_results.get('recommendations', [])
    if recommendations:
        print(f"\nRecommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    
    # Issues
    issues = validation_results.get('issues', [])
    if issues:
        print(f"\nCritical Issues:")
        for issue in issues:
            print(f"  ❌ {issue}")
    
    # Warnings
    warnings = validation_results.get('warnings', [])
    if warnings:
        print(f"\nWarnings:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
    
    # Success status
    success = validation_results.get('validation_success', False)
    if success:
        print(f"\n✅ Validation completed successfully!")
    else:
        print(f"\n❌ Validation failed!")
        error = validation_results.get('error', 'Unknown error')
        print(f"   Error: {error}")
    
    # Save results to file
    output_file = f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {output_file}")
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Symbols Analyzed: {validation_results.get('symbols_analyzed', 0)}")
    print(f"Overall Health Score: {health_score:.1f}%")
    print(f"Validation Time: {validation_time:.2f} seconds")
    print(f"Success: {success}")
    
    if health_score >= 80:
        print("🎉 Excellent coverage! System is ready for production.")
    elif health_score >= 60:
        print("👍 Good coverage with room for improvement.")
    else:
        print("⚠️  Coverage needs significant improvement before production.")
    
    return validation_results

def test_validation_with_sample():
    """Test validation with a smaller sample for faster testing"""
    print("\n" + "=" * 80)
    print("SAMPLE VALIDATION TEST (30 symbols)")
    print("=" * 80)
    
    validator = EnhancedValidator()
    symbol_loader = SymbolLoader()
    
    # Get a sample of symbols
    all_symbols = symbol_loader.get_all_symbols()
    sample_symbols = all_symbols[:30]  # First 30 symbols
    
    print(f"Testing with {len(sample_symbols)} symbols...")
    
    start_time = time.time()
    validation_results = validator.run_comprehensive_validation(sample_symbols)
    end_time = time.time()
    
    print(f"Sample validation completed in {end_time - start_time:.2f} seconds")
    print(f"Health Score: {validation_results.get('overall_health_score', 0):.1f}%")
    
    return validation_results

if __name__ == "__main__":
    try:
        # Run full validation
        results = test_enhanced_validation()
        
        # Optionally run sample validation
        if len(sys.argv) > 1 and sys.argv[1] == "--sample":
            test_validation_with_sample()
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 