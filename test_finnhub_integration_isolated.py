#!/usr/bin/env python3

import sys
import os
import shutil
from datetime import datetime

print("🔍 Testing Finnhub Integration (Isolated)")
print("=========================================")

def setup_test_environment():
    """Set up test environment with DUMMY API keys"""
    if os.path.exists('.env.backup'):
        os.remove('.env.backup')
    
    if os.path.exists('.env'):
        shutil.copy('.env', '.env.backup')
    
    shutil.copy('test_env_dummy.env', '.env')
    
    os.environ['ALPHA_VANTAGE_API_KEY'] = 'DUMMY'
    os.environ['THE_NEWS_API_API_KEY'] = 'DUMMY'
    os.environ['OPENAI_API_KEY'] = 'DUMMY'
    os.environ['RAPIDAPI_KEY'] = 'DUMMY'
    os.environ['BIZTOC_API_KEY'] = 'DUMMY'
    os.environ['FINNHUB_API_KEY'] = 'DUMMY'
    os.environ['FMP_API_KEY'] = 'DUMMY'
    os.environ['NEWSDATA_IO_API_KEY'] = 'DUMMY'
    os.environ['LOG_LEVEL'] = 'INFO'
    
    print("✅ Test environment set up with DUMMY API keys")

def restore_environment():
    """Restore original environment"""
    if os.path.exists('.env.backup'):
        shutil.move('.env.backup', '.env')
        print("✅ Original environment restored")
    elif os.path.exists('.env'):
        os.remove('.env')

def test_imports():
    """Test that imports work with DUMMY API keys"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        
        import importlib
        if 'data_collection.news_collector' in sys.modules:
            importlib.reload(sys.modules['data_collection.news_collector'])
        
        from data_collection.news_collector import NewsCollector
        print("✅ NewsCollector import successful with DUMMY keys")
        return True
    except Exception as e:
        print(f"❌ NewsCollector import failed: {e}")
        return False

def test_finnhub_methods():
    """Test Finnhub integration methods"""
    try:
        import importlib
        if 'data_collection.news_collector' in sys.modules:
            importlib.reload(sys.modules['data_collection.news_collector'])
        
        from data_collection.news_collector import NewsCollector
        news_collector = NewsCollector()
        
        print("Testing method existence...")
        
        if hasattr(news_collector, 'get_comprehensive_company_news'):
            print("✅ get_comprehensive_company_news method exists")
        else:
            print("❌ get_comprehensive_company_news method missing")
            return False
        
        if hasattr(news_collector, '_create_comprehensive_summary'):
            print("✅ _create_comprehensive_summary method exists")
        else:
            print("❌ _create_comprehensive_summary method missing")
            return False
        
        if hasattr(news_collector, 'get_company_news_summary'):
            print("✅ get_company_news_summary method exists")
        else:
            print("❌ get_company_news_summary method missing")
            return False
        
        print("Testing method calls with DUMMY data...")
        
        try:
            result = news_collector.get_comprehensive_company_news("AAPL", "Apple Inc.", 2.5)
            if isinstance(result, list):
                print("✅ get_comprehensive_company_news returns list")
            else:
                print(f"⚠️  get_comprehensive_company_news returns {type(result)}")
        except Exception as e:
            print(f"❌ get_comprehensive_company_news failed: {e}")
            return False
        
        try:
            summary = news_collector.get_company_news_summary("AAPL", "Apple Inc.", 2.5)
            if isinstance(summary, str):
                print("✅ get_company_news_summary returns string")
            else:
                print(f"⚠️  get_company_news_summary returns {type(summary)}")
        except Exception as e:
            print(f"❌ get_company_news_summary failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Finnhub method testing failed: {e}")
        return False

def test_dummy_data_handling():
    """Test that DUMMY API keys trigger mock data"""
    try:
        import importlib
        if 'data_collection.news_collector' in sys.modules:
            importlib.reload(sys.modules['data_collection.news_collector'])
        
        from data_collection.news_collector import NewsCollector
        news_collector = NewsCollector()
        
        dummy_news = news_collector._get_dummy_news()
        if isinstance(dummy_news, list) and len(dummy_news) > 0:
            print("✅ _get_dummy_news returns mock data")
            
            first_article = dummy_news[0]
            required_fields = ['title', 'description', 'url', 'source', 'published_at', 'relevance_score']
            
            for field in required_fields:
                if field in first_article:
                    print(f"✅ Mock article has {field}")
                else:
                    print(f"❌ Mock article missing {field}")
                    return False
            
            return True
        else:
            print("❌ _get_dummy_news failed to return mock data")
            return False
            
    except Exception as e:
        print(f"❌ Dummy data handling test failed: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid inputs"""
    try:
        import importlib
        if 'data_collection.news_collector' in sys.modules:
            importlib.reload(sys.modules['data_collection.news_collector'])
        
        from data_collection.news_collector import NewsCollector
        news_collector = NewsCollector()
        
        try:
            result = news_collector.get_comprehensive_company_news("", "Empty Company", 0.0)
            print("✅ Handles empty symbol gracefully")
        except Exception as e:
            print(f"⚠️  Empty symbol handling: {e}")
        
        try:
            result = news_collector.get_comprehensive_company_news("INVALID_SYMBOL_12345", "Invalid Company", 5.0)
            print("✅ Handles invalid symbol gracefully")
        except Exception as e:
            print(f"⚠️  Invalid symbol handling: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def run_all_tests():
    """Run all Finnhub integration tests"""
    setup_test_environment()
    
    try:
        tests = [
            ("Import Test", test_imports),
            ("Finnhub Methods Test", test_finnhub_methods),
            ("Dummy Data Handling Test", test_dummy_data_handling),
            ("Error Handling Test", test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        
        print(f"\n{'='*50}")
        print(f"Finnhub Integration Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ All Finnhub integration tests PASSED")
            return True
        else:
            print("❌ Some Finnhub integration tests FAILED")
            return False
            
    finally:
        restore_environment()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
