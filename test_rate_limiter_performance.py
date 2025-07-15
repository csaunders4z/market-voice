#!/usr/bin/env python3
"""
Performance test for rate limiter improvements
Tests both sync and async rate limiting to verify efficiency gains
"""
import asyncio
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.rate_limiter import RateLimiter


def mock_api_call(item):
    """Mock API call that simulates processing time"""
    time.sleep(0.01)  # Simulate 10ms API call
    return f"processed_{item}"


async def mock_api_call_async(item):
    """Mock async API call that simulates processing time"""
    await asyncio.sleep(0.01)  # Simulate 10ms API call
    return f"processed_{item}"


def test_sync_rate_limiter():
    """Test synchronous rate limiter performance"""
    print("Testing synchronous rate limiter...")
    
    rate_limiter = RateLimiter()
    test_items = [f"item_{i}" for i in range(20)]
    
    start_time = time.time()
    results = rate_limiter.batch_process(
        items=test_items,
        batch_size=5,
        batch_delay=0.1,
        process_func=mock_api_call,
        api_name="test_sync"
    )
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"Sync processing: {len(results)}/{len(test_items)} items in {duration:.2f}s")
    return duration, len(results)


async def test_async_rate_limiter():
    """Test asynchronous rate limiter performance"""
    print("Testing asynchronous rate limiter...")
    
    rate_limiter = RateLimiter()
    test_items = [f"item_{i}" for i in range(20)]
    
    def sync_wrapper(item):
        return mock_api_call(item)
    
    start_time = time.time()
    results = await rate_limiter.batch_process_async(
        items=test_items,
        batch_size=5,
        batch_delay=0.1,
        process_func=sync_wrapper,
        api_name="test_async"
    )
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"Async processing: {len(results)}/{len(test_items)} items in {duration:.2f}s")
    return duration, len(results)


def test_rate_limit_enforcement():
    """Test that rate limits are still properly enforced"""
    print("Testing rate limit enforcement...")
    
    rate_limiter = RateLimiter()
    
    api_name = "test_enforcement"
    base_delay = 0.5
    
    start_time = time.time()
    rate_limiter._wait_for_rate_limit(api_name, base_delay)
    first_call_time = time.time()
    
    rate_limiter._wait_for_rate_limit(api_name, base_delay)
    second_call_time = time.time()
    
    time_between_calls = second_call_time - first_call_time
    print(f"Time between rate-limited calls: {time_between_calls:.2f}s (expected: ~{base_delay}s)")
    
    assert time_between_calls >= base_delay * 0.8, f"Rate limiting not working: {time_between_calls}s < {base_delay * 0.8}s"
    print("✅ Rate limiting enforcement working correctly")


async def test_async_rate_limit_enforcement():
    """Test that async rate limits are properly enforced"""
    print("Testing async rate limit enforcement...")
    
    rate_limiter = RateLimiter()
    
    api_name = "test_async_enforcement"
    base_delay = 0.5
    
    start_time = time.time()
    await rate_limiter._wait_for_rate_limit_async(api_name, base_delay)
    first_call_time = time.time()
    
    await rate_limiter._wait_for_rate_limit_async(api_name, base_delay)
    second_call_time = time.time()
    
    time_between_calls = second_call_time - first_call_time
    print(f"Time between async rate-limited calls: {time_between_calls:.2f}s (expected: ~{base_delay}s)")
    
    assert time_between_calls >= base_delay * 0.8, f"Async rate limiting not working: {time_between_calls}s < {base_delay * 0.8}s"
    print("✅ Async rate limiting enforcement working correctly")


async def main():
    """Run all performance tests"""
    print("=" * 60)
    print("RATE LIMITER PERFORMANCE TEST")
    print("=" * 60)
    
    test_rate_limit_enforcement()
    await test_async_rate_limit_enforcement()
    
    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)
    
    sync_duration, sync_results = test_sync_rate_limiter()
    async_duration, async_results = await test_async_rate_limiter()
    
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"Sync results: {sync_results} items in {sync_duration:.2f}s")
    print(f"Async results: {async_results} items in {async_duration:.2f}s")
    
    if async_duration < sync_duration:
        improvement = ((sync_duration - async_duration) / sync_duration) * 100
        print(f"✅ Async improvement: {improvement:.1f}% faster")
    else:
        print("⚠️  Async performance similar to sync (expected for small batches)")
    
    assert sync_results == async_results, f"Result count mismatch: sync={sync_results}, async={async_results}"
    print("✅ Both methods processed same number of items")
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
