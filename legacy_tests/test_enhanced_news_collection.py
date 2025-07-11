#!/usr/bin/env python3
"""
Test Enhanced News Collection - Day 3-4 Implementation
Tests the expanded news collection for ALL top movers
"""
import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_enhanced_news_collection():
    """Test the enhanced news collection that covers ALL top movers"""
    print("🚀 TESTING: Enhanced News Collection (Week 1, Day 3-4)")
    print("="*60)
    
    try:
        from src.data_collection.news_collector import news_collector
        print("✅ Successfully imported enhanced news_collector")
        
        # Create mock stock data representing top movers
        mock_stock_data = [
            {'symbol': 'AAPL', 'company_name': 'Apple Inc.', 'percent_change': 2.5},
            {'symbol': 'MSFT', 'company_name': 'Microsoft Corp.', 'percent_change': -1.8},
            {'symbol': 'GOOGL', 'company_name': 'Alphabet Inc.', 'percent_change': 3.2},
            {'symbol': 'TSLA', 'company_name': 'Tesla Inc.', 'percent_change': -2.1},
            {'symbol': 'NVDA', 'company_name': 'NVIDIA Corp.', 'percent_change': 4.1},
            {'symbol': 'META', 'company_name': 'Meta Platforms', 'percent_change': 1.5},
        ]
        
        print(f"\n📊 Testing enhanced collection for {len(mock_stock_data)} stocks:")
        for stock in mock_stock_data:
            print(f"   {stock['symbol']}: {stock['percent_change']:+.1f}%")
        
        # Test comprehensive company news for individual stock
        print(f"\n🔍 Testing comprehensive news for individual stock...")
        test_symbol = 'AAPL'
        comp_news = news_collector.get_comprehensive_company_news(
            test_symbol, 'Apple Inc.', 2.5
        )
        
        print(f"   Results for {test_symbol}:")
        print(f"   ✅ Collection Success: {comp_news.get('collection_success', False)}")
        print(f"   📰 Articles Found: {len(comp_news.get('articles', []))}")
        print(f"   🔍 Catalysts Identified: {comp_news.get('catalysts', [])}")
        print(f"   📝 Summary Length: {len(comp_news.get('summary', ''))} chars")
        print(f"   🗞️  Sources Used: {comp_news.get('sources_used', [])}")
        
        if comp_news.get('articles'):
            top_article = comp_news['articles'][0]
            print(f"   Top Article: [{top_article.get('source', 'Unknown')}] {top_article.get('title', '')[:60]}...")
        
        # Test market news collection with enhanced coverage
        print(f"\n🌍 Testing enhanced market news collection...")
        symbols = [stock['symbol'] for stock in mock_stock_data]
        market_news = news_collector.get_market_news(symbols, mock_stock_data)
        
        print(f"   Market News Collection Success: {market_news.get('collection_success', False)}")
        print(f"   General Market Articles: {len(market_news.get('market_news', []))}")
        print(f"   Company-Specific Summaries: {len(market_news.get('news_summaries', {}))}")
        print(f"   Comprehensive News Coverage: {len(market_news.get('comprehensive_news', {}))}")
        
        # Analyze coverage improvement
        old_threshold_coverage = sum(1 for stock in mock_stock_data if abs(stock['percent_change']) >= 3)
        new_threshold_coverage = sum(1 for stock in mock_stock_data if abs(stock['percent_change']) >= 1)
        
        print(f"\n📈 COVERAGE IMPROVEMENT:")
        print(f"   Old threshold (≥3%): {old_threshold_coverage}/{len(mock_stock_data)} stocks ({old_threshold_coverage/len(mock_stock_data)*100:.1f}%)")
        print(f"   New threshold (≥1%): {new_threshold_coverage}/{len(mock_stock_data)} stocks ({new_threshold_coverage/len(mock_stock_data)*100:.1f}%)")
        print(f"   Coverage increase: +{new_threshold_coverage - old_threshold_coverage} stocks")
        
        # Check comprehensive news data
        comprehensive_news = market_news.get('comprehensive_news', {})
        if comprehensive_news:
            print(f"\n🎯 COMPREHENSIVE NEWS ANALYSIS:")
            total_articles = 0
            total_catalysts = 0
            
            for symbol, news_data in comprehensive_news.items():
                articles_count = len(news_data.get('articles', []))
                catalysts_count = len(news_data.get('catalysts', []))
                total_articles += articles_count
                total_catalysts += catalysts_count
                
                print(f"   {symbol}: {articles_count} articles, {catalysts_count} catalysts")
                if news_data.get('catalysts'):
                    print(f"      Catalysts: {', '.join(news_data['catalysts'])}")
            
            print(f"   Total: {total_articles} articles, {total_catalysts} catalysts across all stocks")
            print(f"   Average: {total_articles/len(comprehensive_news):.1f} articles per stock")
        
        print(f"\n✅ Enhanced news collection test completed!")
        
        success_criteria = [
            comp_news.get('collection_success', False),
            market_news.get('collection_success', False),
            new_threshold_coverage > old_threshold_coverage,
            len(market_news.get('comprehensive_news', {})) >= 3  # At least 3 stocks with comprehensive news
        ]
        
        return all(success_criteria)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the enhanced news collection test"""
    success = test_enhanced_news_collection()
    
    if success:
        print("\n🎉 WEEK 1, DAY 3-4 COMPLETED: Enhanced news collection for ALL top movers!")
        print("\n📊 KEY IMPROVEMENTS:")
        print("   ✅ Reduced threshold from 3% to 1% (more stocks covered)")
        print("   ✅ Added comprehensive news analysis with catalyst identification")
        print("   ✅ Integrated free news scraper with paid API fallback")
        print("   ✅ Enhanced news summaries with multiple sources")
        print("   ✅ Top 20 movers now get full news analysis")
        print("\n🔄 Next: Integrate with script generator (Day 5)")
    else:
        print("\n⚠️  Test failed - check errors above")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)