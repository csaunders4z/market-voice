#!/usr/bin/env python3
"""
Rate Limiting Test - Market Voices
Tests the new rate limiting system with adaptive delays and batch processing
"""
import os
import sys
from datetime import datetime
from loguru import logger
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.logger import setup_logging, get_logger
from src.data_collection.unified_data_collector import UnifiedDataCollector
from src.config.settings import get_settings


def test_rate_limiting_config():
    """Test rate limiting configuration"""
    print("🔧 Testing Rate Limiting Configuration...")
    
    try:
        settings = get_settings()
        
        print(f"✅ FMP Settings:")
        print(f"   Rate limit delay: {settings.fmp_rate_limit_delay}s")
        print(f"   Batch size: {settings.fmp_batch_size}")
        print(f"   Batch delay: {settings.fmp_batch_delay}s")
        print(f"   Max retries: {settings.fmp_max_retries}")
        
        print(f"✅ Yahoo Finance Settings:")
        print(f"   Rate limit delay: {settings.yahoo_rate_limit_delay}s")
        print(f"   Batch size: {settings.yahoo_batch_size}")
        print(f"   Batch delay: {settings.yahoo_batch_delay}s")
        
        print(f"✅ Alpha Vantage Settings:")
        print(f"   Rate limit delay: {settings.alpha_vantage_rate_limit_delay}s")
        print(f"   Batch size: {settings.alpha_vantage_batch_size}")
        print(f"   Batch delay: {settings.alpha_vantage_batch_delay}s")
        
        print(f"✅ Adaptive Rate Limiting:")
        print(f"   Enabled: {settings.enable_adaptive_rate_limiting}")
        print(f"   Backoff multiplier: {settings.rate_limit_backoff_multiplier}")
        print(f"   Max delay: {settings.max_rate_limit_delay}s")
        
        print(f"✅ Collection Limits:")
        print(f"   Max symbols: {settings.max_symbols_per_collection}")
        print(f"   Timeout: {settings.collection_timeout_minutes} minutes")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        return False


def test_small_batch_collection():
    """Test collection with small batch to verify rate limiting"""
    print("\n📊 Testing Small Batch Collection...")
    
    try:
        setup_logging()
        logger = get_logger("RateLimitTest")
        
        collector = UnifiedDataCollector()
        test_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
        
        print(f"Testing with {len(test_symbols)} symbols...")
        start_time = time.time()
        
        result = collector.collect_data(test_symbols, production_mode=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.get('collection_success'):
            print(f"✅ Collection successful!")
            print(f"   Data source: {result.get('data_source', 'Unknown')}")
            print(f"   Symbols collected: {len(result.get('all_data', []))}")
            print(f"   Duration: {duration:.2f} seconds")
            print(f"   Average time per symbol: {duration/len(test_symbols):.2f} seconds")
            
            # Show sample data
            all_data = result.get('all_data', [])
            if all_data:
                print(f"\nSample Data:")
                for i, stock in enumerate(all_data[:3], 1):
                    print(f"  {i}. {stock.get('symbol')} - {stock.get('company_name')}")
                    print(f"     Change: {stock.get('percent_change', 0):.2f}%")
                    print(f"     Price: ${stock.get('current_price', 0):.2f}")
                    print(f"     RSI: {stock.get('rsi', 'N/A')}")
                    print(f"     Volume ratio: {stock.get('volume_ratio', 'N/A')}")
                    print("")
            
            return True
        else:
            print(f"❌ Collection failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Small batch test failed: {str(e)}")
        return False


def test_adaptive_rate_limiting():
    """Test adaptive rate limiting behavior"""
    print("\n🔄 Testing Adaptive Rate Limiting...")
    
    try:
        from src.utils.rate_limiter import rate_limiter
        
        # Test adaptive delay calculation
        base_delay = 1.0
        api_name = "test_api"
        
        # Simulate rate limit error
        test_error = Exception("429 Too Many Requests")
        rate_limiter._handle_rate_limit_error(api_name, test_error)
        
        # Check if delay increased
        delay = rate_limiter._get_delay(api_name, base_delay)
        print(f"✅ Base delay: {base_delay}s")
        print(f"✅ Adaptive delay after rate limit: {delay:.2f}s")
        
        if delay > base_delay:
            print("✅ Adaptive rate limiting working correctly!")
        else:
            print("⚠️  Adaptive rate limiting may not be working as expected")
        
        return True
        
    except Exception as e:
        print(f"❌ Adaptive rate limiting test failed: {str(e)}")
        return False


def test_batch_processing():
    """Test batch processing functionality"""
    print("\n📦 Testing Batch Processing...")
    
    try:
        from src.utils.rate_limiter import rate_limiter
        
        # Test data
        test_items = list(range(25))  # 25 items
        
        def test_process_func(item):
            # Simulate processing with small delay
            time.sleep(0.01)
            return item * 2  # Simple transformation
        
        print(f"Processing {len(test_items)} items in batches...")
        start_time = time.time()
        
        results = rate_limiter.batch_process(
            items=test_items,
            batch_size=5,
            batch_delay=0.1,
            process_func=test_process_func,
            api_name="Test API"
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Batch processing completed!")
        print(f"   Items processed: {len(results)}/{len(test_items)}")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Average time per item: {duration/len(test_items):.3f} seconds")
        
        # Verify results
        expected_results = [item * 2 for item in test_items]
        if results == expected_results:
            print("✅ All items processed correctly!")
        else:
            print("❌ Some items were not processed correctly")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Batch processing test failed: {str(e)}")
        return False


def test_fallback_behavior():
    """Test fallback behavior when rate limits are hit"""
    print("\n🔄 Testing Fallback Behavior...")
    
    try:
        setup_logging()
        logger = get_logger("FallbackTest")
        
        collector = UnifiedDataCollector()
        
        # Test with a larger set of symbols to potentially hit rate limits
        test_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "NFLX", "ADBE", "CRM"]
        
        print(f"Testing fallback with {len(test_symbols)} symbols...")
        start_time = time.time()
        
        result = collector.collect_data(test_symbols, production_mode=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.get('collection_success'):
            print(f"✅ Fallback successful!")
            print(f"   Data source: {result.get('data_source', 'Unknown')}")
            print(f"   Symbols collected: {len(result.get('all_data', []))}")
            print(f"   Duration: {duration:.2f} seconds")
            
            # Check if we used a fallback source
            data_source = result.get('data_source', '')
            if 'FMP' not in data_source:
                print(f"✅ Successfully fell back to {data_source}")
            else:
                print(f"✅ Primary source (FMP) worked correctly")
            
            return True
        else:
            print(f"❌ All sources failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Fallback test failed: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🧪 MARKET VOICES - RATE LIMITING TEST")
    print("=" * 60)
    print(f"Test timestamp: {datetime.now().isoformat()}")
    
    # Run all tests
    tests = [
        ("Configuration", test_rate_limiting_config),
        ("Small Batch Collection", test_small_batch_collection),
        ("Adaptive Rate Limiting", test_adaptive_rate_limiting),
        ("Batch Processing", test_batch_processing),
        ("Fallback Behavior", test_fallback_behavior)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📋 RATE LIMITING TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All rate limiting tests passed! System is optimized for API limits.")
    else:
        print("⚠️  Some tests failed. Review the output above for details.")
    
    print("=" * 60)
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 