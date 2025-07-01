#!/usr/bin/env python3
"""
Test script for the new Stock News Scraper
Tests the comprehensive news collection functionality
"""
import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.data_collection.stock_news_scraper import stock_news_scraper, NewsArticle
    print("✅ Successfully imported stock_news_scraper")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Installing required dependencies...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "beautifulsoup4", "requests", "--break-system-packages"], check=False)
    
    # Try import again
    try:
        from src.data_collection.stock_news_scraper import stock_news_scraper, NewsArticle
        print("✅ Successfully imported stock_news_scraper after installing dependencies")
    except ImportError as e2:
        print(f"❌ Still failed to import: {e2}")
        sys.exit(1)

def test_single_stock_news_collection():
    """Test news collection for a single stock"""
    print("\n" + "="*60)
    print("🧪 TESTING: Single Stock News Collection")
    print("="*60)
    
    test_symbol = "AAPL"
    print(f"Testing news collection for {test_symbol}...")
    
    try:
        # Test individual scrapers
        print(f"\n📰 Testing individual news sources for {test_symbol}:")
        
        # Test Yahoo Finance
        print("1. Testing Yahoo Finance...")
        yahoo_articles = stock_news_scraper.scrape_yahoo_finance_news(test_symbol)
        print(f"   ✅ Yahoo Finance: {len(yahoo_articles)} articles")
        
        # Test Seeking Alpha
        print("2. Testing Seeking Alpha...")
        sa_articles = stock_news_scraper.scrape_seeking_alpha_articles(test_symbol)
        print(f"   ✅ Seeking Alpha: {len(sa_articles)} articles")
        
        # Test MarketWatch
        print("3. Testing MarketWatch...")
        mw_articles = stock_news_scraper.scrape_marketwatch_stories(test_symbol)
        print(f"   ✅ MarketWatch: {len(mw_articles)} articles")
        
        # Test Benzinga
        print("4. Testing Benzinga...")
        bz_articles = stock_news_scraper.scrape_benzinga_news(test_symbol)
        print(f"   ✅ Benzinga: {len(bz_articles)} articles")
        
        # Test Finviz
        print("5. Testing Finviz...")
        fv_articles = stock_news_scraper.scrape_finviz_news(test_symbol)
        print(f"   ✅ Finviz: {len(fv_articles)} articles")
        
        # Test comprehensive collection
        print(f"\n🔄 Testing comprehensive news collection for {test_symbol}...")
        all_articles = stock_news_scraper.get_comprehensive_stock_news(test_symbol)
        
        print(f"\n📊 RESULTS for {test_symbol}:")
        print(f"   Total articles collected: {len(all_articles)}")
        
        if all_articles:
            print(f"   Top 3 articles by relevance:")
            for i, article in enumerate(all_articles[:3], 1):
                print(f"   {i}. [{article.source}] {article.title[:80]}...")
                print(f"      Relevance: {article.relevance_score:.1f}, Words: {article.word_count}")
        
        return len(all_articles) > 0
        
    except Exception as e:
        print(f"❌ Error in single stock test: {str(e)}")
        return False

def test_multiple_stocks_news_collection():
    """Test news collection for multiple stocks"""
    print("\n" + "="*60)
    print("🧪 TESTING: Multiple Stocks News Collection")
    print("="*60)
    
    test_symbols = ["AAPL", "MSFT", "GOOGL"]
    print(f"Testing news collection for {test_symbols}...")
    
    try:
        results = stock_news_scraper.get_news_for_multiple_stocks(test_symbols, max_articles_per_stock=10)
        
        print(f"\n📊 RESULTS for multiple stocks:")
        total_articles = 0
        for symbol, articles in results.items():
            print(f"   {symbol}: {len(articles)} articles")
            total_articles += len(articles)
            
            if articles:
                top_article = articles[0]
                print(f"      Top: [{top_article.source}] {top_article.title[:60]}...")
        
        print(f"   Total articles across all stocks: {total_articles}")
        
        return total_articles > 0
        
    except Exception as e:
        print(f"❌ Error in multiple stocks test: {str(e)}")
        return False

def test_news_article_quality():
    """Test the quality and structure of collected articles"""
    print("\n" + "="*60)
    print("🧪 TESTING: News Article Quality")
    print("="*60)
    
    test_symbol = "TSLA"  # Usually has lots of news
    
    try:
        articles = stock_news_scraper.get_comprehensive_stock_news(test_symbol, max_articles=5)
        
        if not articles:
            print(f"⚠️  No articles found for {test_symbol}")
            return False
        
        print(f"Testing quality of {len(articles)} articles for {test_symbol}:")
        
        quality_metrics = {
            'has_title': 0,
            'has_description': 0,
            'has_url': 0,
            'has_source': 0,
            'has_relevance_score': 0,
            'symbol_mentioned': 0
        }
        
        for i, article in enumerate(articles, 1):
            print(f"\n   Article {i}:")
            print(f"   Title: {article.title[:80]}...")
            print(f"   Source: {article.source}")
            print(f"   URL: {article.url[:60]}...")
            print(f"   Description: {article.description[:100]}..." if article.description else "   Description: None")
            print(f"   Relevance Score: {article.relevance_score:.1f}")
            print(f"   Word Count: {article.word_count}")
            print(f"   Published: {article.published_at}")
            
            # Check quality metrics
            if article.title and len(article.title) > 5:
                quality_metrics['has_title'] += 1
            if article.description and len(article.description) > 10:
                quality_metrics['has_description'] += 1
            if article.url and article.url.startswith('http'):
                quality_metrics['has_url'] += 1
            if article.source:
                quality_metrics['has_source'] += 1
            if article.relevance_score > 0:
                quality_metrics['has_relevance_score'] += 1
            if test_symbol.lower() in article.title.lower() or test_symbol.lower() in article.description.lower():
                quality_metrics['symbol_mentioned'] += 1
        
        print(f"\n📊 QUALITY METRICS:")
        total_articles = len(articles)
        for metric, count in quality_metrics.items():
            percentage = (count / total_articles) * 100
            print(f"   {metric}: {count}/{total_articles} ({percentage:.1f}%)")
        
        # Calculate overall quality score
        overall_quality = sum(quality_metrics.values()) / (len(quality_metrics) * total_articles) * 100
        print(f"   Overall Quality Score: {overall_quality:.1f}%")
        
        return overall_quality > 60  # At least 60% quality
        
    except Exception as e:
        print(f"❌ Error in quality test: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 MARKET VOICES - NEWS SCRAPER TESTING")
    print("="*60)
    
    test_results = []
    
    # Test 1: Single stock news collection
    test_results.append(test_single_stock_news_collection())
    
    # Test 2: Multiple stocks news collection
    test_results.append(test_multiple_stocks_news_collection())
    
    # Test 3: News article quality
    test_results.append(test_news_article_quality())
    
    # Summary
    print("\n" + "="*60)
    print("📊 TESTING SUMMARY")
    print("="*60)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    test_names = [
        "Single Stock News Collection",
        "Multiple Stocks News Collection", 
        "News Article Quality"
    ]
    
    for i, (test_name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{i+1}. {test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! News scraper is working correctly.")
        print("\n🔄 Next steps:")
        print("   1. Integrate with existing news collector")
        print("   2. Expand news collection to ALL top movers") 
        print("   3. Add catalyst identification")
        return True
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)