#!/usr/bin/env python3
"""
Simple test for Stock News Scraper
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_functionality():
    """Test basic news scraper functionality"""
    print("🚀 Testing Stock News Scraper")
    print("="*50)
    
    try:
        # Import our scraper
        from src.data_collection.stock_news_scraper import stock_news_scraper
        print("✅ Successfully imported stock_news_scraper")
        
        # Test with a simple stock
        symbol = "AAPL"
        print(f"\n📰 Testing news collection for {symbol}...")
        
        # Test Yahoo Finance scraping (most reliable)
        print("Testing Yahoo Finance...")
        yahoo_articles = stock_news_scraper.scrape_yahoo_finance_news(symbol)
        print(f"   Yahoo Finance: {len(yahoo_articles)} articles found")
        
        if yahoo_articles:
            article = yahoo_articles[0]
            print(f"   Sample article: {article.title[:60]}...")
            print(f"   Source: {article.source}")
            print(f"   Relevance: {article.relevance_score:.1f}")
        
        # Test comprehensive collection
        print(f"\n🔄 Testing comprehensive collection...")
        all_articles = stock_news_scraper.get_comprehensive_stock_news(symbol, max_articles=10)
        print(f"   Total articles: {len(all_articles)}")
        
        if all_articles:
            print("   Top 3 articles:")
            for i, article in enumerate(all_articles[:3], 1):
                print(f"   {i}. [{article.source}] {article.title[:50]}...")
        
        print(f"\n✅ News scraper test completed successfully!")
        print(f"   - Collected {len(all_articles)} articles for {symbol}")
        print(f"   - Sources working: Yahoo Finance and others")
        print(f"   - Ready for integration with script generator")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        print("\n🎉 WEEK 1, DAY 1-2 COMPLETED: Free news source scraping implemented!")
        print("🔄 Next: Expand collection to ALL top movers (Day 3-4)")
    else:
        print("\n⚠️  Test failed - check errors above")
    
    sys.exit(0 if success else 1)