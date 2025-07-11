#!/usr/bin/env python3
"""
Debug script to test news API response and date filtering
"""
import requests
from datetime import datetime, timedelta
from src.config.settings import get_settings

def test_newsapi_response():
    """Test NewsAPI response directly"""
    settings = get_settings()
    api_key = settings.news_api_key
    
    print(f"Testing NewsAPI with key: {api_key[:10]}...")
    
    # Test 1: With domain restrictions
    print("\n=== Test 1: With domain restrictions ===")
    url = "https://newsapi.org/v2/everything"
    params = {
        'q': 'AAPL',
        'from': (datetime.now() - timedelta(hours=24)).isoformat(),
        'sortBy': 'publishedAt',
        'language': 'en',
        'apiKey': api_key,
        'pageSize': 5,
        'domains': 'reuters.com,bloomberg.com,marketwatch.com,cnbc.com,wsj.com,seekingalpha.com,benzinga.com,yahoo.com'
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        articles = data.get('articles', [])
        
        print(f"NewsAPI response status: {data.get('status')}")
        print(f"Total articles returned: {len(articles)}")
        
    except Exception as e:
        print(f"Error testing NewsAPI: {e}")
    
    # Test 2: Without domain restrictions
    print("\n=== Test 2: Without domain restrictions ===")
    params = {
        'q': 'AAPL',
        'from': (datetime.now() - timedelta(hours=24)).isoformat(),
        'sortBy': 'publishedAt',
        'language': 'en',
        'apiKey': api_key,
        'pageSize': 5
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        articles = data.get('articles', [])
        
        print(f"NewsAPI response status: {data.get('status')}")
        print(f"Total articles returned: {len(articles)}")
        
        if articles:
            print("\nFirst article:")
            article = articles[0]
            print(f"  Title: {article.get('title', 'N/A')}")
            print(f"  Published: {article.get('publishedAt', 'N/A')}")
            print(f"  Source: {article.get('source', {}).get('name', 'N/A')}")
            
            # Test date filtering
            published_at = article.get('publishedAt', '')
            if published_at:
                try:
                    article_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    is_today = article_date.date() == today.date()
                    print(f"  Is today: {is_today}")
                    print(f"  Article date: {article_date.date()}")
                    print(f"  Today: {today.date()}")
                except Exception as e:
                    print(f"  Date parsing error: {e}")
        else:
            print("No articles returned from NewsAPI")
            
    except Exception as e:
        print(f"Error testing NewsAPI: {e}")
    
    # Test 3: Broader search term
    print("\n=== Test 3: Broader search term (stock market) ===")
    params = {
        'q': 'stock market',
        'from': (datetime.now() - timedelta(hours=24)).isoformat(),
        'sortBy': 'publishedAt',
        'language': 'en',
        'apiKey': api_key,
        'pageSize': 5
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        articles = data.get('articles', [])
        
        print(f"NewsAPI response status: {data.get('status')}")
        print(f"Total articles returned: {len(articles)}")
        
        if articles:
            print("\nFirst article:")
            article = articles[0]
            print(f"  Title: {article.get('title', 'N/A')}")
            print(f"  Published: {article.get('publishedAt', 'N/A')}")
            print(f"  Source: {article.get('source', {}).get('name', 'N/A')}")
            
    except Exception as e:
        print(f"Error testing NewsAPI: {e}")

if __name__ == "__main__":
    test_newsapi_response() 