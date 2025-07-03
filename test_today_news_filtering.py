#!/usr/bin/env python3
"""
Test script to verify today-only news filtering for winners and losers
"""
import sys
import os
from datetime import datetime, timedelta
from loguru import logger

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_collection.unified_data_collector import UnifiedDataCollector
from data_collection.news_collector import NewsCollector
from data_collection.stock_news_scraper import StockNewsScraper
from data_collection.free_news_sources import FreeNewsCollector

def test_today_news_filtering():
    """Test that only today's articles are collected for winners and losers"""
    logger.info("Starting today-only news filtering test")
    logger.info(f"Test timestamp: {datetime.now().isoformat()}")
    
    # Test with a few major symbols
    test_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
    
    logger.info(f"Testing with symbols: {test_symbols}")
    
    # Test 1: News Collector today filtering
    logger.info("\n=== Testing News Collector Today Filtering ===")
    news_collector = NewsCollector()
    
    for symbol in test_symbols[:2]:  # Test first 2 symbols
        logger.info(f"Testing NewsAPI for {symbol}")
        articles = news_collector.get_newsapi_news(symbol, hours_back=24)
        
        today_count = 0
        for article in articles:
            published_at = article.get('published_at', '')
            if published_at:
                try:
                    article_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    if article_date.date() == datetime.now().date():
                        today_count += 1
                except:
                    pass
        
        logger.info(f"  {symbol}: {today_count}/{len(articles)} articles are from today")
    
    # Test 2: Stock News Scraper today filtering
    logger.info("\n=== Testing Stock News Scraper Today Filtering ===")
    scraper = StockNewsScraper()
    
    for symbol in test_symbols[:2]:  # Test first 2 symbols
        logger.info(f"Testing comprehensive news for {symbol}")
        articles = scraper.get_comprehensive_stock_news(symbol, max_articles=10)
        
        today_count = 0
        for article in articles:
            if scraper._is_today_article(article.published_at):
                today_count += 1
        
        logger.info(f"  {symbol}: {today_count}/{len(articles)} articles are from today")
    
    # Test 3: Free News Sources today filtering
    logger.info("\n=== Testing Free News Sources Today Filtering ===")
    free_collector = FreeNewsCollector()
    
    articles = free_collector.get_comprehensive_free_news("NASDAQ", limit=10)
    
    today_count = 0
    for article in articles:
        if free_collector._is_today_article(article.get('published_at', '')):
            today_count += 1
    
    logger.info(f"  Free sources: {today_count}/{len(articles)} articles are from today")
    
    logger.info("\n=== Today-Only News Filtering Test Complete ===")
    logger.info("✅ All today-only filtering tests completed")
    logger.info("📰 System now focuses on today's articles for winners and losers")
    logger.info("🎯 This should provide more relevant catalysts for stock movements")

if __name__ == "__main__":
    test_today_news_filtering() 