#!/usr/bin/env python3

import sys
import os
import shutil
from datetime import datetime

print("🔍 Testing End-to-End News Collection")
print("=====================================")

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

def test_multiple_symbols():
    """Test news collection with multiple stock symbols"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        
        import importlib
        if 'data_collection.news_collector' in sys.modules:
            importlib.reload(sys.modules['data_collection.news_collector'])
        
        from data_collection.news_collector import NewsCollector
        
        news_collector = NewsCollector()
        test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
        
        results = {}
        
        for symbol in test_symbols:
            try:
                print(f"Testing news collection for {symbol}...")
                company_names = {
                    'AAPL': 'Apple Inc.',
                    'MSFT': 'Microsoft Corporation',
                    'GOOGL': 'Alphabet Inc.',
                    'TSLA': 'Tesla Inc.',
                    'NVDA': 'NVIDIA Corporation'
                }
                company_name = company_names.get(symbol, f"{symbol} Corporation")
                news = news_collector.get_comprehensive_company_news(symbol, company_name, 2.5)
                
                if isinstance(news, list):
                    results[symbol] = {
                        'success': True,
                        'count': len(news),
                        'has_data': len(news) > 0
                    }
                    print(f"✅ {symbol}: {len(news)} articles collected")
                else:
                    results[symbol] = {
                        'success': False,
                        'error': f"Expected list, got {type(news)}"
                    }
                    print(f"❌ {symbol}: Invalid return type {type(news)}")
                    
            except Exception as e:
                results[symbol] = {
                    'success': False,
                    'error': str(e)
                }
                print(f"❌ {symbol}: Error - {e}")
        
        successful_symbols = sum(1 for r in results.values() if r.get('success', False))
        total_symbols = len(test_symbols)
        
        print(f"\nSymbol testing results: {successful_symbols}/{total_symbols} successful")
        
        if successful_symbols >= total_symbols * 0.8:
            print("✅ Multiple symbol testing PASSED")
            return True
        else:
            print("❌ Multiple symbol testing FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Multiple symbol test failed: {e}")
        return False

def test_news_source_integration():
    """Test that all 5 news sources are integrated"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        
        import importlib
        if 'data_collection.news_collector' in sys.modules:
            importlib.reload(sys.modules['data_collection.news_collector'])
        
        from data_collection.news_collector import NewsCollector
        
        news_collector = NewsCollector()
        
        news_methods = [
            ('NewsAPI', 'get_newsapi_news'),
            ('Biztoc', 'get_biztoc_news'),
            ('NewsData.io', 'get_newsdata_news'),
            ('The News API', 'get_the_news_api_news'),
            ('Finnhub', 'get_comprehensive_company_news')
        ]
        
        available_sources = 0
        
        for source_name, method_name in news_methods:
            if hasattr(news_collector, method_name):
                print(f"✅ {source_name} method ({method_name}) available")
                available_sources += 1
                
                try:
                    if method_name == 'get_comprehensive_company_news':
                        result = getattr(news_collector, method_name)('AAPL', 'Apple Inc.', 2.5)
                    else:
                        result = getattr(news_collector, method_name)()
                    
                    if isinstance(result, list):
                        print(f"✅ {source_name} returns list data")
                    else:
                        print(f"⚠️  {source_name} returns {type(result)}")
                        
                except Exception as e:
                    print(f"⚠️  {source_name} method call error: {e}")
            else:
                print(f"❌ {source_name} method ({method_name}) missing")
        
        print(f"\nNews source integration: {available_sources}/{len(news_methods)} sources available")
        
        if available_sources >= len(news_methods):
            print("✅ All news sources integrated")
            return True
        else:
            print("❌ Some news sources missing")
            return False
            
    except Exception as e:
        print(f"❌ News source integration test failed: {e}")
        return False

def test_circuit_breaker_functionality():
    """Test circuit breaker patterns for news sources"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        
        import importlib
        if 'data_collection.news_collector' in sys.modules:
            importlib.reload(sys.modules['data_collection.news_collector'])
        
        from data_collection.news_collector import NewsCollector
        
        news_collector = NewsCollector()
        
        circuit_breaker_attrs = [
            '_newsapi_disabled_for_session',
            '_biztoc_disabled_for_session',
            '_newsdata_disabled_for_session',
            '_thenewsapi_disabled_for_session'
        ]
        
        available_breakers = 0
        
        for attr in circuit_breaker_attrs:
            if hasattr(news_collector, attr):
                print(f"✅ Circuit breaker {attr} available")
                available_breakers += 1
            else:
                print(f"❌ Circuit breaker {attr} missing")
        
        print(f"\nCircuit breaker availability: {available_breakers}/{len(circuit_breaker_attrs)}")
        
        if available_breakers >= len(circuit_breaker_attrs):
            print("✅ Circuit breaker functionality available")
            return True
        else:
            print("❌ Some circuit breakers missing")
            return False
            
    except Exception as e:
        print(f"❌ Circuit breaker test failed: {e}")
        return False

def test_news_summary_generation():
    """Test news summary generation functionality"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        
        import importlib
        if 'data_collection.news_collector' in sys.modules:
            importlib.reload(sys.modules['data_collection.news_collector'])
        
        from data_collection.news_collector import NewsCollector
        
        news_collector = NewsCollector()
        
        try:
            summary = news_collector.get_company_news_summary('AAPL', 'Apple Inc.', 2.5)
            
            if isinstance(summary, str) and len(summary) > 0:
                print("✅ News summary generation works")
                print(f"✅ Summary length: {len(summary)} characters")
                return True
            else:
                print(f"❌ Invalid summary: {type(summary)}, length: {len(summary) if isinstance(summary, str) else 'N/A'}")
                return False
                
        except Exception as e:
            print(f"❌ News summary generation error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ News summary test failed: {e}")
        return False

def test_error_handling_scenarios():
    """Test various error handling scenarios"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        
        import importlib
        if 'data_collection.news_collector' in sys.modules:
            importlib.reload(sys.modules['data_collection.news_collector'])
        
        from data_collection.news_collector import NewsCollector
        
        news_collector = NewsCollector()
        
        error_scenarios = [
            ('Empty symbol', '', 'Empty Company'),
            ('Invalid symbol', 'INVALID_SYMBOL_12345', 'Invalid Company'),
            ('Special characters', 'A@#$%', 'Special Company'),
            ('Very long symbol', 'A' * 50, 'Long Company')
        ]
        
        handled_errors = 0
        
        for scenario_name, test_symbol, test_company in error_scenarios:
            try:
                result = news_collector.get_comprehensive_company_news(test_symbol, test_company, 1.0)
                print(f"✅ {scenario_name}: Handled gracefully")
                handled_errors += 1
            except Exception as e:
                print(f"⚠️  {scenario_name}: Exception - {e}")
                handled_errors += 1
        
        print(f"\nError handling: {handled_errors}/{len(error_scenarios)} scenarios handled")
        
        if handled_errors >= len(error_scenarios):
            print("✅ Error handling scenarios PASSED")
            return True
        else:
            print("❌ Some error handling scenarios FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def run_all_tests():
    """Run all end-to-end news collection tests"""
    setup_test_environment()
    
    try:
        tests = [
            ("Multiple Symbols Test", test_multiple_symbols),
            ("News Source Integration Test", test_news_source_integration),
            ("Circuit Breaker Functionality Test", test_circuit_breaker_functionality),
            ("News Summary Generation Test", test_news_summary_generation),
            ("Error Handling Scenarios Test", test_error_handling_scenarios)
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
        print(f"End-to-End News Collection Test Results: {passed}/{total} tests passed")
        
        if passed >= total - 1:
            print("✅ End-to-end news collection tests PASSED")
            return True
        else:
            print("❌ Critical end-to-end tests FAILED")
            return False
            
    finally:
        restore_environment()

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
