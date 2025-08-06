"""
Test script for Finnhub news integration in Market Voice.

This script tests the Finnhub news collection functionality to ensure it's working as expected.
"""
import os
import sys
import json
from datetime import datetime, timedelta
from loguru import logger

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_collection.news_collector import NewsCollector
from src.data_collection.finnhub_data_collector import finnhub_data_collector

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

def test_finnhub_market_news():
    """Test fetching market news from Finnhub."""
    logger.info("Testing Finnhub market news...")
    
    # Initialize the collector
    collector = NewsCollector()
    
    try:
        # Test market news
        logger.info("Fetching market news...")
        market_news = collector.get_finnhub_news('market')
        
        # Basic validation
        assert isinstance(market_news, list), "Market news should be a list"
        logger.success(f"Retrieved {len(market_news)} market news articles")
        
        if market_news:
            # Check article structure
            article = market_news[0]
            required_fields = ['title', 'url', 'published_at', 'source']
            for field in required_fields:
                assert field in article, f"Missing required field: {field}"
                assert article[field], f"Empty value for required field: {field}"
            
            # Log a sample article (first 100 chars of title)
            sample_title = article['title'][:100] + '...' if len(article['title']) > 100 else article['title']
            logger.info(f"Sample article: {sample_title}")
            logger.info(f"Published: {article.get('published_at')}")
            logger.info(f"Source: {article.get('source')}")
            
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

def test_finnhub_company_news():
    """Test fetching company news from Finnhub."""
    logger.info("\nTesting Finnhub company news...")
    
    # Initialize the collector
    collector = NewsCollector()
    
    try:
        # Test with a well-known company (Apple)
        symbol = 'AAPL'
        logger.info(f"Fetching news for {symbol}...")
        company_news = collector.get_finnhub_news(symbol)
        
        # Basic validation
        assert isinstance(company_news, list), "Company news should be a list"
        logger.success(f"Retrieved {len(company_news)} news articles for {symbol}")
        
        if company_news:
            # Check article structure
            article = company_news[0]
            required_fields = ['title', 'url', 'published_at', 'source']
            for field in required_fields:
                assert field in article, f"Missing required field: {field}"
                assert article[field], f"Empty value for required field: {field}"
            
            # Log a sample article
            sample_title = article['title'][:100] + '...' if len(article['title']) > 100 else article['title']
            logger.info(f"Sample article: {sample_title}")
            logger.info(f"Published: {article.get('published_at')}")
            logger.info(f"Source: {article.get('source')}")
            
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

def test_comprehensive_analysis():
    """Test the comprehensive analysis with Finnhub integration."""
    logger.info("\nTesting comprehensive analysis with Finnhub...")
    
    # Initialize the collector
    collector = NewsCollector()
    
    try:
        # Test with a well-known company (Microsoft)
        symbol = 'MSFT'
        logger.info(f"Running comprehensive analysis for {symbol}...")
        analysis = collector.get_comprehensive_analysis(symbol=symbol)
        
        # Basic validation
        required_fields = ['symbol', 'articles', 'summary', 'sources_used', 'collection_success']
        for field in required_fields:
            assert field in analysis, f"Missing required field in analysis: {field}"
        
        logger.success(f"Analysis completed. Collection success: {analysis['collection_success']}")
        logger.info(f"Sources used: {', '.join(analysis.get('sources_used', [])) or 'None'}")
        logger.info(f"Articles found: {len(analysis.get('articles', []))}")
        
        if analysis.get('articles'):
            # Log a sample article
            article = analysis['articles'][0]
            sample_title = article['title'][:100] + '...' if len(article['title']) > 100 else article['title']
            logger.info(f"Sample article: {sample_title}")
            logger.info(f"Source: {article.get('source')}")
        
        # Check if we have a non-empty summary
        assert analysis.get('summary'), "Empty summary generated"
        logger.info(f"Summary length: {len(analysis['summary'])} characters")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all Finnhub integration tests."""
    logger.info("=" * 80)
    logger.info("STARTING FINNHUB INTEGRATION TESTS")
    logger.info("=" * 80)
    
    test_results = {
        'market_news': test_finnhub_market_news(),
        'company_news': test_finnhub_company_news(),
        'comprehensive_analysis': test_comprehensive_analysis()
    }
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    all_passed = True
    for test_name, passed in test_results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{test_name:25} {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.success("All Finnhub integration tests passed!")
    else:
        logger.error("Some Finnhub integration tests failed. Check the logs for details.")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()
