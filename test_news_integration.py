#!/usr/bin/env python3
"""
Test script to verify news integration in Market Voices
Ensures news articles are properly attached to each stock for script generation
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data_collection.unified_data_collector import unified_collector
from src.data_collection.comprehensive_collector import comprehensive_collector
from loguru import logger

def test_unified_collector_news_integration():
    """Test that unified collector properly attaches news articles to stocks"""
    print("=" * 60)
    print("TESTING UNIFIED COLLECTOR NEWS INTEGRATION")
    print("=" * 60)
    
    # Test with a small number of symbols to avoid API rate limits
    test_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    
    print(f"Testing with symbols: {test_symbols}")
    
    try:
        # Collect data using unified collector
        result = unified_collector.collect_data(symbols=test_symbols, production_mode=False)
        
        if not result.get('collection_success'):
            print(f"❌ Data collection failed: {result.get('error', 'Unknown error')}")
            return False
        
        winners = result.get('winners', [])
        losers = result.get('losers', [])
        all_data = result.get('all_data', [])
        
        print(f"✅ Data collection successful")
        print(f"   Winners: {len(winners)}")
        print(f"   Losers: {len(losers)}")
        print(f"   Total data: {len(all_data)}")
        
        # Check if news articles are attached to stocks
        stocks_with_news = 0
        total_news_articles = 0
        
        for stock in winners + losers:
            symbol = stock.get('symbol', '')
            news_articles = stock.get('news_articles', [])
            news_analysis = stock.get('news_analysis', '')
            news_sources = stock.get('news_sources', [])
            
            if news_articles:
                stocks_with_news += 1
                total_news_articles += len(news_articles)
                print(f"   {symbol}: {len(news_articles)} news articles, {len(news_sources)} sources")
                
                # Show first article details
                if news_articles:
                    first_article = news_articles[0]
                    print(f"     First article: {first_article.get('title', 'No title')[:50]}... ({first_article.get('source', 'Unknown')})")
        
        print(f"\nNews Integration Summary:")
        print(f"   Stocks with news articles: {stocks_with_news}/{len(winners + losers)}")
        print(f"   Total news articles: {total_news_articles}")
        
        # Validate that news data structure is correct
        for stock in winners + losers:
            symbol = stock.get('symbol', '')
            
            # Check required fields exist
            assert 'news_articles' in stock, f"Stock {symbol} missing news_articles field"
            assert 'news_analysis' in stock, f"Stock {symbol} missing news_analysis field"
            assert 'news_sources' in stock, f"Stock {symbol} missing news_sources field"
            
            # Check data types
            assert isinstance(stock['news_articles'], list), f"Stock {symbol} news_articles should be a list"
            assert isinstance(stock['news_analysis'], str), f"Stock {symbol} news_analysis should be a string"
            assert isinstance(stock['news_sources'], list), f"Stock {symbol} news_sources should be a list"
        
        print("✅ News integration test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_comprehensive_collector_news_integration():
    """Test that comprehensive collector properly attaches news articles to stocks"""
    print("\n" + "=" * 60)
    print("TESTING COMPREHENSIVE COLLECTOR NEWS INTEGRATION")
    print("=" * 60)
    
    try:
        # Test with a small number of symbols to avoid API rate limits
        test_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
        
        print(f"Testing with symbols: {test_symbols}")
        
        # Override symbols in comprehensive collector for testing
        original_symbols = comprehensive_collector.symbol_lists['all_symbols']
        comprehensive_collector.symbol_lists['all_symbols'] = test_symbols
        
        try:
            # Collect data using comprehensive collector
            result = comprehensive_collector.collect_comprehensive_data(production_mode=False)
            
            if not result.get('collection_success'):
                print(f"❌ Data collection failed: {result.get('error', 'Unknown error')}")
                return False
            
            winners = result.get('winners', [])
            losers = result.get('losers', [])
            
            print(f"✅ Data collection successful")
            print(f"   Winners: {len(winners)}")
            print(f"   Losers: {len(losers)}")
            
            # Check if news articles are attached to stocks
            stocks_with_news = 0
            total_news_articles = 0
            
            for stock in winners + losers:
                symbol = stock.get('symbol', '')
                news_articles = stock.get('news_articles', [])
                news_analysis = stock.get('news_analysis', '')
                news_sources = stock.get('news_sources', [])
                
                if news_articles:
                    stocks_with_news += 1
                    total_news_articles += len(news_articles)
                    print(f"   {symbol}: {len(news_articles)} news articles, {len(news_sources)} sources")
            
            print(f"\nNews Integration Summary:")
            print(f"   Stocks with news articles: {stocks_with_news}/{len(winners + losers)}")
            print(f"   Total news articles: {total_news_articles}")
            
            # Validate that news data structure is correct
            for stock in winners + losers:
                symbol = stock.get('symbol', '')
                
                # Check required fields exist
                assert 'news_articles' in stock, f"Stock {symbol} missing news_articles field"
                assert 'news_analysis' in stock, f"Stock {symbol} missing news_analysis field"
                assert 'news_sources' in stock, f"Stock {symbol} missing news_sources field"
            
            print("✅ Comprehensive collector news integration test PASSED")
            return True
            
        finally:
            # Restore original symbols
            comprehensive_collector.symbol_lists['all_symbols'] = original_symbols
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

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
        
        print(f"Prompt contains news articles section: {has_news_articles}")
        print(f"Prompt contains news sources: {has_news_sources}")
        print(f"Prompt contains news analysis: {has_news_analysis}")
        
        # Validate that news data is properly formatted in prompt
        assert has_news_articles, "Script prompt should contain news articles section"
        assert has_news_sources, "Script prompt should contain news sources"
        assert has_news_analysis, "Script prompt should contain news analysis"
        
        print("✅ Script generator news access test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def main():
    """Run all news integration tests"""
    print("MARKET VOICES - NEWS INTEGRATION TEST")
    print("Testing compliance with TODO item 2: Leverage News Data for WHY Analysis")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run all tests
        test1_passed = test_unified_collector_news_integration()
        test2_passed = test_comprehensive_collector_news_integration()
        test3_passed = test_script_generator_news_access()
        
        if test1_passed and test2_passed and test3_passed:
            print("\n" + "=" * 60)
            print("🎉 ALL NEWS INTEGRATION TESTS PASSED!")
            print("✅ News articles are properly attached to each stock")
            print("✅ Script generator can access news data for WHY analysis")
            print("✅ News integration is working across all collectors")
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