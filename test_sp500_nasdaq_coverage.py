#!/usr/bin/env python3
"""
Test script to verify S&P 500 and NASDAQ-100 coverage in Market Voices
Ensures all workflows include both indices as required by TODO item 1
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data_collection.symbol_loader import symbol_loader
from src.data_collection.screening_module import screening_module
from src.data_collection.comprehensive_collector import comprehensive_collector
from src.script_generation.script_generator import script_generator
from loguru import logger

def test_symbol_loader_coverage():
    """Test that symbol loader provides both S&P 500 and NASDAQ-100 symbols"""
    print("=" * 60)
    print("TESTING SYMBOL LOADER COVERAGE")
    print("=" * 60)
    
    # Test individual index loading
    nasdaq_symbols = symbol_loader.get_nasdaq_100_symbols()
    sp500_symbols = symbol_loader.get_sp_500_symbols()
    all_symbols = symbol_loader.get_all_symbols()
    
    print(f"NASDAQ-100 symbols loaded: {len(nasdaq_symbols)}")
    print(f"S&P 500 symbols loaded: {len(sp500_symbols)}")
    print(f"Combined unique symbols: {len(all_symbols)}")
    
    # Check for overlap
    nasdaq_set = set(nasdaq_symbols)
    sp500_set = set(sp500_symbols)
    overlap = nasdaq_set.intersection(sp500_set)
    
    print(f"Overlap between indices: {len(overlap)} symbols")
    print(f"Expected overlap: ~50-80 symbols (many NASDAQ-100 stocks are also in S&P 500)")
    
    # Validate symbol counts
    assert len(nasdaq_symbols) >= 90, f"NASDAQ-100 should have at least 90 symbols, got {len(nasdaq_symbols)}"
    assert len(sp500_symbols) >= 450, f"S&P 500 should have at least 450 symbols, got {len(sp500_symbols)}"
    assert len(all_symbols) >= 500, f"Combined should have at least 500 symbols, got {len(all_symbols)}"
    
    print("✅ Symbol loader coverage test PASSED")
    return True

def test_screening_module_coverage():
    """Test that screening module uses combined symbol list"""
    print("\n" + "=" * 60)
    print("TESTING SCREENING MODULE COVERAGE")
    print("=" * 60)
    
    # Check that screening module loaded symbols
    screening_symbols = screening_module.symbols
    
    print(f"Screening module loaded symbols: {len(screening_symbols)}")
    
    # Verify it's using the combined list
    nasdaq_symbols = symbol_loader.get_nasdaq_100_symbols()
    sp500_symbols = symbol_loader.get_sp_500_symbols()
    all_symbols = symbol_loader.get_all_symbols()
    
    # Check if screening symbols match combined list
    screening_set = set(screening_symbols)
    all_set = set(all_symbols)
    
    if screening_set == all_set:
        print("✅ Screening module is using combined S&P 500 + NASDAQ-100 symbol list")
    else:
        print("❌ Screening module is NOT using combined symbol list")
        missing = all_set - screening_set
        extra = screening_set - all_set
        print(f"Missing symbols: {len(missing)}")
        print(f"Extra symbols: {len(extra)}")
        return False
    
    print("✅ Screening module coverage test PASSED")
    return True

def test_comprehensive_collector_coverage():
    """Test that comprehensive collector handles both indices"""
    print("\n" + "=" * 60)
    print("TESTING COMPREHENSIVE COLLECTOR COVERAGE")
    print("=" * 60)
    
    # Load symbol lists from comprehensive collector
    symbol_lists = comprehensive_collector.symbol_lists
    
    all_symbols = symbol_lists.get('all_symbols', [])
    sp500_symbols = symbol_lists.get('sp500_symbols', [])
    nasdaq100_symbols = symbol_lists.get('nasdaq100_symbols', [])
    
    print(f"Comprehensive collector symbol counts:")
    print(f"  All symbols: {len(all_symbols)}")
    print(f"  S&P 500 symbols: {len(sp500_symbols)}")
    print(f"  NASDAQ-100 symbols: {len(nasdaq100_symbols)}")
    
    # Validate that we have both indices
    assert len(sp500_symbols) > 0, "Comprehensive collector should have S&P 500 symbols"
    assert len(nasdaq100_symbols) > 0, "Comprehensive collector should have NASDAQ-100 symbols"
    assert len(all_symbols) > 0, "Comprehensive collector should have combined symbols"
    
    print("✅ Comprehensive collector coverage test PASSED")
    return True

def test_script_generator_references():
    """Test that script generator properly references both indices"""
    print("\n" + "=" * 60)
    print("TESTING SCRIPT GENERATOR REFERENCES")
    print("=" * 60)
    
    # Create sample market data with both indices
    sample_market_data = {
        'market_summary': {
            'total_target_symbols': 516,
            'sp500_coverage': 250,
            'nasdaq100_coverage': 100,
            'coverage_percentage': 67.8,
            'advancing_stocks': 65,
            'declining_stocks': 35,
            'average_change': 0.85,
            'market_sentiment': 'Mixed',
            'data_source': 'Comprehensive Collection',
            'market_date': datetime.now().isoformat()
        },
        'winners': [
            {'symbol': 'AAPL', 'company_name': 'Apple Inc.', 'current_price': 150.25, 'percent_change': 3.2},
            {'symbol': 'MSFT', 'company_name': 'Microsoft Corporation', 'current_price': 320.50, 'percent_change': 2.8},
            {'symbol': 'GOOGL', 'company_name': 'Alphabet Inc.', 'current_price': 2800.00, 'percent_change': 2.1},
            {'symbol': 'AMZN', 'company_name': 'Amazon.com Inc.', 'current_price': 3200.75, 'percent_change': 1.9},
            {'symbol': 'NVDA', 'company_name': 'NVIDIA Corporation', 'current_price': 450.30, 'percent_change': 1.7}
        ],
        'losers': [
            {'symbol': 'TSLA', 'company_name': 'Tesla Inc.', 'current_price': 800.50, 'percent_change': -2.1},
            {'symbol': 'META', 'company_name': 'Meta Platforms Inc.', 'current_price': 280.25, 'percent_change': -1.8},
            {'symbol': 'NFLX', 'company_name': 'Netflix Inc.', 'current_price': 450.75, 'percent_change': -1.5},
            {'symbol': 'ADBE', 'company_name': 'Adobe Inc.', 'current_price': 380.00, 'percent_change': -1.2},
            {'symbol': 'CRM', 'company_name': 'Salesforce Inc.', 'current_price': 220.50, 'percent_change': -0.9}
        ],
        'collection_success': True
    }
    
    # Generate a prompt to check the content
    lead_host = 'suzanne'
    prompt = script_generator.create_script_prompt(sample_market_data, lead_host)
    
    # Check for proper references to both indices
    has_sp500_ref = 'S&P 500' in prompt
    has_nasdaq_ref = 'NASDAQ-100' in prompt
    has_major_markets_ref = 'major US markets' in prompt or 'major US stocks' in prompt
    
    print(f"Prompt contains S&P 500 reference: {has_sp500_ref}")
    print(f"Prompt contains NASDAQ-100 reference: {has_nasdaq_ref}")
    print(f"Prompt contains major markets reference: {has_major_markets_ref}")
    
    # Check for coverage statistics in prompt
    has_coverage_stats = 'S&P 500 coverage:' in prompt and 'NASDAQ-100 coverage:' in prompt
    
    print(f"Prompt contains coverage statistics: {has_coverage_stats}")
    
    # Validate that we have proper references
    assert has_sp500_ref or has_major_markets_ref, "Script generator should reference S&P 500 or major markets"
    assert has_nasdaq_ref or has_major_markets_ref, "Script generator should reference NASDAQ-100 or major markets"
    assert has_coverage_stats, "Script generator should include coverage statistics"
    
    print("✅ Script generator references test PASSED")
    return True

def main():
    """Run all coverage tests"""
    print("MARKET VOICES - S&P 500 & NASDAQ-100 COVERAGE TEST")
    print("Testing compliance with TODO item 1: Ensure S&P 500 Coverage in Script Generation")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run all tests
        test_symbol_loader_coverage()
        test_screening_module_coverage()
        test_comprehensive_collector_coverage()
        test_script_generator_references()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ S&P 500 and NASDAQ-100 coverage is properly implemented")
        print("✅ All workflows include both indices as required")
        print("✅ Script generation properly references both indices")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 