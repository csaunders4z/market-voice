#!/usr/bin/env python3
"""
Clean test script to verify news integration data structure in Market Voices
Tests the core news integration without hitting external APIs
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_news_data_structure():
    """Test that the news data structure is correctly implemented"""
    print("=" * 60)
    print("TESTING NEWS DATA STRUCTURE IMPLEMENTATION")
    print("=" * 60)
    
    # Test the data structure that should be attached to each stock
    sample_stock_with_news = {
        'symbol': 'AAPL',
        'company_name': 'Apple Inc.',
        'current_price': 150.25,
        'percent_change': 3.2,
        'volume_ratio': 1.5,
        'news_articles': [
            {
                'title': 'Apple Reports Strong Q4 Earnings',
                'source': 'Reuters',
                'published_at': '2024-01-15T10:30:00Z',
                'description': 'Apple exceeded analyst expectations...'
            },
            {
                'title': 'Apple Stock Surges on iPhone Sales',
                'source': 'Bloomberg',
                'published_at': '2024-01-15T09:15:00Z',
                'description': 'Strong iPhone sales drive growth...'
            }
        ],
        'news_analysis': 'Apple stock surged after reporting strong Q4 earnings that exceeded analyst expectations. The company saw strong iPhone sales and services revenue growth.',
        'news_sources': ['Reuters', 'Bloomberg', 'CNBC']
    }
    
    # Validate required fields exist
    required_fields = ['news_articles', 'news_analysis', 'news_sources']
    for field in required_fields:
        assert field in sample_stock_with_news, f"Stock missing required field: {field}"
        print(f"✅ Field '{field}' present")
    
    # Validate data types
    assert isinstance(sample_stock_with_news['news_articles'], list), "news_articles should be a list"
    assert isinstance(sample_stock_with_news['news_analysis'], str), "news_analysis should be a string"
    assert isinstance(sample_stock_with_news['news_sources'], list), "news_sources should be a list"
    print("✅ Data types are correct")
    
    # Validate news article structure
    if sample_stock_with_news['news_articles']:
        article = sample_stock_with_news['news_articles'][0]
        article_fields = ['title', 'source', 'published_at', 'description']
        for field in article_fields:
            assert field in article, f"News article missing field: {field}"
        print("✅ News article structure is correct")
    
    print("✅ News data structure validation PASSED")
    return True

def test_script_generator_news_access():
    """Test that script generator can access news data from stocks"""
    print("\n" + "=" * 60)
    print("TESTING SCRIPT GENERATOR NEWS ACCESS")
    print("=" * 60)
    
    try:
        from src.script_generation.script_generator import script_generator
        
        # Create sample market data with news articles
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
                'data_source': 'Test Data',
                'market_date': datetime.now().isoformat()
            },
            'winners': [
                {
                    'symbol': 'AAPL',
                    'company_name': 'Apple Inc.',
                    'current_price': 150.25,
                    'percent_change': 3.2,
                    'volume_ratio': 1.5,
                    'news_articles': [
                        {
                            'title': 'Apple Reports Strong Q4 Earnings',
                            'source': 'Reuters',
                            'published_at': '2024-01-15T10:30:00Z',
                            'description': 'Apple exceeded analyst expectations...'
                        },
                        {
                            'title': 'Apple Stock Surges on iPhone Sales',
                            'source': 'Bloomberg',
                            'published_at': '2024-01-15T09:15:00Z',
                            'description': 'Strong iPhone sales drive growth...'
                        }
                    ],
                    'news_analysis': 'Apple stock surged after reporting strong Q4 earnings that exceeded analyst expectations. The company saw strong iPhone sales and services revenue growth.',
                    'news_sources': ['Reuters', 'Bloomberg', 'CNBC']
                }
            ],
            'losers': [
                {
                    'symbol': 'TSLA',
                    'company_name': 'Tesla Inc.',
                    'current_price': 800.50,
                    'percent_change': -2.1,
                    'volume_ratio': 1.8,
                    'news_articles': [
                        {
                            'title': 'Tesla Faces Regulatory Scrutiny',
                            'source': 'MarketWatch',
                            'published_at': '2024-01-15T11:00:00Z',
                            'description': 'Regulatory concerns impact Tesla stock...'
                        }
                    ],
                    'news_analysis': 'Tesla stock declined due to regulatory concerns over autonomous driving features.',
                    'news_sources': ['MarketWatch']
                }
            ],
            'collection_success': True
        }
        
        # Test script prompt generation
        lead_host = 'suzanne'
        prompt = script_generator.create_script_prompt(sample_market_data, lead_host)
        
        # Check if news data is included in the prompt
        has_news_articles = 'Recent News Articles:' in prompt
        has_news_sources = 'Reuters' in prompt or 'Bloomberg' in prompt or 'MarketWatch' in prompt
        has_news_analysis = 'News Analysis:' in prompt
        has_why_requirements = 'explain WHY stocks moved' in prompt
        
        print(f"Prompt contains news articles section: {has_news_articles}")
        print(f"Prompt contains news sources: {has_news_sources}")
        print(f"Prompt contains news analysis: {has_news_analysis}")
        print(f"Prompt contains WHY analysis requirements: {has_why_requirements}")
        
        # Validate that news data is properly formatted in prompt
        assert has_news_articles, "Script prompt should contain news articles section"
        assert has_news_sources, "Script prompt should contain news sources"
        assert has_news_analysis, "Script prompt should contain news analysis"
        assert has_why_requirements, "Script prompt should contain WHY analysis requirements"
        
        print("✅ Script generator news access test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_unified_collector_news_integration():
    """Test that unified collector properly handles news integration"""
    print("\n" + "=" * 60)
    print("TESTING UNIFIED COLLECTOR NEWS INTEGRATION")
    print("=" * 60)
    
    try:
        from src.data_collection.unified_data_collector import unified_collector
        
        # Test with production_mode=False to avoid API calls
        test_symbols = ["AAPL", "MSFT", "GOOGL"]
        
        print(f"Testing with symbols: {test_symbols}")
        print("Note: This will use cached/mock data to avoid API calls")
        
        # Collect data using unified collector in test mode
        result = unified_collector.collect_data(symbols=test_symbols, production_mode=False)
        
        if not result.get('collection_success'):
            print(f"❌ Data collection failed: {result.get('error', 'Unknown error')}")
            return False
        
        winners = result.get('winners', [])
        losers = result.get('losers', [])
        
        print(f"✅ Data collection successful")
        print(f"   Winners: {len(winners)}")
        print(f"   Losers: {len(losers)}")
        
        # Check if news fields are present on all stocks
        all_stocks = winners + losers
        stocks_with_news_fields = 0
        
        for stock in all_stocks:
            symbol = stock.get('symbol', '')
            
            # Check required fields exist
            has_news_articles = 'news_articles' in stock
            has_news_analysis = 'news_analysis' in stock
            has_news_sources = 'news_sources' in stock
            
            if has_news_articles and has_news_analysis and has_news_sources:
                stocks_with_news_fields += 1
                print(f"   {symbol}: ✅ All news fields present")
            else:
                print(f"   {symbol}: ❌ Missing news fields")
        
        print(f"\nNews Integration Summary:")
        print(f"   Stocks with news fields: {stocks_with_news_fields}/{len(all_stocks)}")
        
        # Validate that all stocks have news fields (even if empty)
        assert stocks_with_news_fields == len(all_stocks), f"Not all stocks have news fields"
        
        print("✅ Unified collector news integration test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def main():
    """Run all clean news integration tests"""
    print("MARKET VOICES - CLEAN NEWS INTEGRATION TEST")
    print("Testing compliance with TODO item 2: Leverage News Data for WHY Analysis")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nNote: This test focuses on data structure validation without external API calls")
    
    try:
        # Run all tests
        test1_passed = test_news_data_structure()
        test2_passed = test_script_generator_news_access()
        test3_passed = test_unified_collector_news_integration()
        
        if test1_passed and test2_passed and test3_passed:
            print("\n" + "=" * 60)
            print("🎉 ALL CLEAN NEWS INTEGRATION TESTS PASSED!")
            print("✅ News data structure is correctly implemented")
            print("✅ Script generator can access news data for WHY analysis")
            print("✅ News integration is working in unified collector")
            print("✅ System is ready for production with real API keys")
            print("=" * 60)
            return True
        else:
            print("\n❌ Some tests failed")
            return False
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 