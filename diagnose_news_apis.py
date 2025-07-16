#!/usr/bin/env python3
"""
News API Diagnostic Script
Tests each news API individually to identify specific failure points
"""

import os
import sys
import requests
from datetime import datetime, timedelta
from loguru import logger

# Add src to path
sys.path.append('/home/ubuntu/repos/market-voice')

from src.config.settings import get_settings
from src.data_collection.news_collector import NewsCollector
from src.data_collection.finnhub_news_adapter import FinnhubNewsAdapter

def test_api_keys():
    """Test if API keys are configured and valid"""
    settings = get_settings()
    
    print("=== API Key Configuration Test ===")
    
    the_news_api_key = settings.the_news_api_api_key
    print(f"THE_NEWS_API_API_KEY: {'✅ Configured' if the_news_api_key and the_news_api_key != 'DUMMY' else '❌ Missing/Dummy'}")
    
    biztoc_key = os.getenv("BIZTOC_API_KEY", "")
    print(f"BIZTOC_API_KEY: {'✅ Configured' if biztoc_key else '❌ Missing'}")
    
    finnhub_key = settings.finnhub_api_key
    print(f"FINNHUB_API_KEY: {'✅ Configured' if finnhub_key and finnhub_key != 'DUMMY' else '❌ Missing/Dummy'}")
    
    newsdata_key = settings.newsdata_io_api_key
    print(f"NEWSDATA_IO_API_KEY: {'✅ Configured' if newsdata_key and newsdata_key != 'DUMMY' else '❌ Missing/Dummy'}")
    
    print()

def test_individual_apis():
    """Test each news API individually"""
    print("=== Individual API Tests ===")
    
    news_collector = NewsCollector()
    test_symbol = "AAPL"
    
    print(f"Testing NewsAPI for {test_symbol}...")
    try:
        newsapi_results = news_collector.get_newsapi_news(test_symbol, 24)
        print(f"  ✅ NewsAPI: {len(newsapi_results)} articles")
        if newsapi_results:
            print(f"     Sample: {newsapi_results[0].get('title', 'No title')[:50]}...")
    except Exception as e:
        print(f"  ❌ NewsAPI Error: {str(e)}")
    
    print(f"Testing Biztoc for {test_symbol}...")
    try:
        biztoc_results = news_collector.get_biztoc_news(test_symbol, 24)
        print(f"  ✅ Biztoc: {len(biztoc_results)} articles")
        if biztoc_results:
            print(f"     Sample: {biztoc_results[0].get('title', 'No title')[:50]}...")
    except Exception as e:
        print(f"  ❌ Biztoc Error: {str(e)}")
    
    print(f"Testing Finnhub for {test_symbol}...")
    try:
        finnhub_adapter = FinnhubNewsAdapter()
        finnhub_results = finnhub_adapter.get_company_news(test_symbol)
        print(f"  ✅ Finnhub: {len(finnhub_results)} articles")
        if finnhub_results:
            print(f"     Sample: {finnhub_results[0].get('title', 'No title')[:50]}...")
    except Exception as e:
        print(f"  ❌ Finnhub Error: {str(e)}")
    
    print(f"Testing NewsData.io for {test_symbol}...")
    try:
        newsdata_results = news_collector.get_newsdata_news(test_symbol, 24)
        print(f"  ✅ NewsData.io: {len(newsdata_results)} articles")
        if newsdata_results:
            print(f"     Sample: {newsdata_results[0].get('title', 'No title')[:50]}...")
    except Exception as e:
        print(f"  ❌ NewsData.io Error: {str(e)}")
    
    print()

def test_circuit_breaker_status():
    """Check if any APIs are disabled due to circuit breakers"""
    print("=== Circuit Breaker Status ===")
    
    news_collector = NewsCollector()
    
    print(f"NewsAPI disabled: {news_collector._newsapi_disabled_for_session} (failures: {news_collector._newsapi_consecutive_failures})")
    print(f"Biztoc disabled: {news_collector._biztoc_disabled_for_session} (failures: {news_collector._biztoc_consecutive_failures})")
    print(f"NewsData.io disabled: {news_collector._newsdata_disabled_for_session} (failures: {news_collector._newsdata_consecutive_failures})")
    print(f"The News API disabled: {news_collector._thenewsapi_disabled_for_session} (failures: {news_collector._thenewsapi_consecutive_failures})")
    
    from src.data_collection.finnhub_news_adapter import finnhub_news_adapter
    print(f"Finnhub disabled: {finnhub_news_adapter._finnhub_news_disabled_for_session} (failures: {finnhub_news_adapter._finnhub_news_consecutive_failures})")
    
    print()

def test_free_news_relevance():
    """Test free news collection and relevance scoring"""
    print("=== Free News Relevance Test ===")
    
    try:
        from src.data_collection.free_news_sources import free_news_collector
        
        free_news = free_news_collector.get_market_news()
        print(f"Free news articles collected: {len(free_news)}")
        
        if free_news:
            for i, article in enumerate(free_news[:3]):
                relevance = article.get('relevance_score', 'N/A')
                title = article.get('title', 'No title')[:60]
                print(f"  Article {i+1}: Relevance={relevance}, Title='{title}...'")
        
        news_collector = NewsCollector()
        test_article = {
            'title': 'Apple Stock Rises on Strong iPhone Sales',
            'description': 'Apple Inc shares gained 3% after reporting better than expected iPhone sales'
        }
        relevance = news_collector._calculate_relevance_score(test_article, 'AAPL')
        print(f"Test relevance calculation for AAPL article: {relevance}")
        
    except Exception as e:
        print(f"❌ Free news test error: {str(e)}")
    
    print()

def test_date_filtering():
    """Test date filtering logic"""
    print("=== Date Filtering Test ===")
    
    now = datetime.now()
    print(f"Current system time: {now}")
    print(f"Current date: {now.date()}")
    
    utc_now = datetime.utcnow()
    print(f"Current UTC time: {utc_now}")
    print(f"UTC date: {utc_now.date()}")
    
    if now.date() == utc_now.date():
        print("✅ Local and UTC dates match")
    else:
        print("⚠️  Local and UTC dates differ - potential timezone filtering issue")
    
    print()

if __name__ == "__main__":
    print("🔍 News API Diagnostic Report")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    test_api_keys()
    test_circuit_breaker_status()
    test_individual_apis()
    test_free_news_relevance()
    test_date_filtering()
    
    print("🏁 Diagnostic Complete")
