#!/usr/bin/env python3
"""
Test Parallel Processing Performance
Compare parallel data collection vs memory-optimized collection
"""
import sys
import os
import time
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_collection.parallel_collector import ParallelCollector
from src.data_collection.memory_optimized_collector import MemoryOptimizedCollector
from src.data_collection.symbol_loader import SymbolLoader
from src.utils.logger import get_logger

def test_parallel_vs_memory_optimized():
    """Compare parallel processing vs memory-optimized collection"""
    print("=" * 80)
    print("PARALLEL PROCESSING PERFORMANCE TEST")
    print("=" * 80)
    
    # Setup logging
    logger = get_logger()
    
    # Initialize components
    parallel_collector = ParallelCollector(max_workers=10, batch_size=20)
    memory_collector = MemoryOptimizedCollector()
    symbol_loader = SymbolLoader()
    
    # Get test symbols
    print("\n1. Loading test symbols...")
    all_symbols = symbol_loader.get_all_symbols()
    test_symbols = all_symbols[:50]  # Test with 50 symbols
    
    print(f"   Testing with {len(test_symbols)} symbols")
    print(f"   Parallel workers: {parallel_collector.max_workers}")
    print(f"   Batch size: {parallel_collector.batch_size}")
    
    # Test Memory-Optimized Collector
    print("\n2. Testing Memory-Optimized Collector...")
    start_time = time.time()
    
    memory_results = memory_collector.collect_data_optimized(
        symbols=test_symbols, 
        production_mode=False
    )
    
    memory_time = time.time() - start_time
    memory_success = memory_results.get('collection_success', False)
    memory_data_count = len(memory_results.get('all_data', []))
    
    print(f"   Memory-Optimized Results:")
    print(f"     Time: {memory_time:.2f} seconds")
    print(f"     Success: {memory_success}")
    print(f"     Data collected: {memory_data_count} symbols")
    
    # Test Parallel Collector
    print("\n3. Testing Parallel Collector...")
    start_time = time.time()
    
    parallel_results = parallel_collector.collect_data_parallel(
        symbols=test_symbols, 
        production_mode=False
    )
    
    parallel_time = time.time() - start_time
    parallel_success = parallel_results.get('collection_success', False)
    parallel_data_count = len(parallel_results.get('all_data', []))
    parallel_stats = parallel_results.get('performance_stats', {})
    
    print(f"   Parallel Results:")
    print(f"     Time: {parallel_time:.2f} seconds")
    print(f"     Success: {parallel_success}")
    print(f"     Data collected: {parallel_data_count} symbols")
    
    if parallel_stats:
        print(f"     Success rate: {parallel_stats.get('success_rate_percent', 0):.1f}%")
        print(f"     Symbols processed: {parallel_stats.get('symbols_processed', 0)}")
        print(f"     Symbols successful: {parallel_stats.get('symbols_successful', 0)}")
        print(f"     Symbols failed: {parallel_stats.get('symbols_failed', 0)}")
        print(f"     Retry count: {parallel_stats.get('retry_count', 0)}")
        print(f"     Memory usage: {parallel_stats.get('memory_usage_mb', 0):.1f} MB")
        print(f"     Memory delta: {parallel_stats.get('memory_delta_mb', 0):.1f} MB")
    
    # Performance Comparison
    print("\n4. PERFORMANCE COMPARISON")
    print("-" * 50)
    
    if memory_success and parallel_success:
        time_improvement = ((memory_time - parallel_time) / memory_time) * 100
        speedup_factor = memory_time / parallel_time if parallel_time > 0 else 0
        
        print(f"Time Improvement: {time_improvement:.1f}%")
        print(f"Speedup Factor: {speedup_factor:.2f}x")
        
        if time_improvement > 0:
            print(f"✅ Parallel processing is {speedup_factor:.2f}x faster!")
        else:
            print(f"⚠️  Parallel processing is {abs(speedup_factor):.2f}x slower")
        
        # Data quality comparison
        memory_data = memory_results.get('all_data', [])
        parallel_data = parallel_results.get('all_data', [])
        
        print(f"\nData Quality Comparison:")
        print(f"  Memory-Optimized: {len(memory_data)} symbols collected")
        print(f"  Parallel: {len(parallel_data)} symbols collected")
        
        # Check for data consistency
        memory_symbols = {item['symbol'] for item in memory_data}
        parallel_symbols = {item['symbol'] for item in parallel_data}
        
        common_symbols = memory_symbols.intersection(parallel_symbols)
        print(f"  Common symbols: {len(common_symbols)}")
        
        if len(common_symbols) > 0:
            # Compare data for common symbols
            memory_dict = {item['symbol']: item for item in memory_data}
            parallel_dict = {item['symbol']: item for item in parallel_data}
            
            differences = 0
            for symbol in common_symbols:
                mem_item = memory_dict[symbol]
                par_item = parallel_dict[symbol]
                
                if (mem_item.get('current_price', 0) != par_item.get('current_price', 0) or
                    mem_item.get('percent_change', 0) != par_item.get('percent_change', 0)):
                    differences += 1
            
            print(f"  Data differences: {differences} symbols")
            
            if differences == 0:
                print("  ✅ Data consistency: Perfect match")
            else:
                print(f"  ⚠️  Data consistency: {differences} differences found")
    
    # Recommendations
    print("\n5. RECOMMENDATIONS")
    print("-" * 50)
    
    if memory_success and parallel_success:
        if time_improvement > 20:
            print("🎉 Parallel processing shows significant performance improvement!")
            print("   Consider using parallel collector for production.")
        elif time_improvement > 0:
            print("👍 Parallel processing shows moderate improvement.")
            print("   Consider using parallel collector for large symbol sets.")
        else:
            print("⚠️  Parallel processing doesn't show improvement for this test.")
            print("   Consider adjusting worker count or batch size.")
        
        # Memory comparison
        if parallel_stats:
            memory_delta = parallel_stats.get('memory_delta_mb', 0)
            if memory_delta < 100:
                print("✅ Memory usage is well controlled.")
            else:
                print(f"⚠️  Memory usage increased by {memory_delta:.1f} MB")
    
    # Save detailed results
    output_file = f"parallel_performance_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    comparison_results = {
        'timestamp': datetime.now().isoformat(),
        'test_symbols_count': len(test_symbols),
        'parallel_workers': parallel_collector.max_workers,
        'batch_size': parallel_collector.batch_size,
        'memory_optimized': {
            'duration_seconds': memory_time,
            'success': memory_success,
            'data_count': memory_data_count,
            'results': memory_results
        },
        'parallel': {
            'duration_seconds': parallel_time,
            'success': parallel_success,
            'data_count': parallel_data_count,
            'performance_stats': parallel_stats,
            'results': parallel_results
        },
        'comparison': {
            'time_improvement_percent': time_improvement if memory_success and parallel_success else 0,
            'speedup_factor': speedup_factor if memory_success and parallel_success else 0,
            'common_symbols_count': len(common_symbols) if memory_success and parallel_success else 0
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(comparison_results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {output_file}")
    
    return comparison_results

def test_parallel_scaling():
    """Test parallel processing with different worker counts"""
    print("\n" + "=" * 80)
    print("PARALLEL SCALING TEST")
    print("=" * 80)
    
    symbol_loader = SymbolLoader()
    test_symbols = symbol_loader.get_all_symbols()[:30]  # 30 symbols
    
    worker_counts = [5, 10, 15, 20]
    results = {}
    
    for workers in worker_counts:
        print(f"\nTesting with {workers} workers...")
        
        collector = ParallelCollector(max_workers=workers, batch_size=20)
        start_time = time.time()
        
        results_data = collector.collect_data_parallel(
            symbols=test_symbols, 
            production_mode=False
        )
        
        duration = time.time() - start_time
        success = results_data.get('collection_success', False)
        data_count = len(results_data.get('all_data', []))
        stats = results_data.get('performance_stats', {})
        
        results[workers] = {
            'duration': duration,
            'success': success,
            'data_count': data_count,
            'success_rate': stats.get('success_rate_percent', 0),
            'memory_usage': stats.get('memory_usage_mb', 0)
        }
        
        print(f"  Duration: {duration:.2f}s, Success: {success}, Data: {data_count}")
    
    # Find optimal worker count
    if results:
        best_workers = min(results.keys(), key=lambda w: results[w]['duration'])
        print(f"\n🎯 Optimal worker count: {best_workers} workers")
        print(f"   Best performance: {results[best_workers]['duration']:.2f} seconds")
    
    return results

def test_full_scale_parallel():
    """Run full-scale parallel collection on all available symbols"""
    print("\n" + "=" * 80)
    print("FULL-SCALE PARALLEL COLLECTION TEST")
    print("=" * 80)
    
    logger = get_logger()
    parallel_collector = ParallelCollector(max_workers=10, batch_size=20)
    symbol_loader = SymbolLoader()
    all_symbols = symbol_loader.get_all_symbols()
    print(f"Collecting data for {len(all_symbols)} symbols...")
    start_time = time.time()
    results = parallel_collector.collect_data_parallel(symbols=all_symbols, production_mode=False)
    duration = time.time() - start_time
    print(f"\nFull-scale collection completed in {duration:.2f} seconds")
    print(f"Success: {results.get('collection_success', False)}")
    print(f"Symbols collected: {len(results.get('all_data', []))}")
    stats = results.get('performance_stats', {})
    if stats:
        print(f"  Success rate: {stats.get('success_rate_percent', 0):.1f}%")
        print(f"  Memory usage: {stats.get('memory_usage_mb', 0):.1f} MB")
        print(f"  Memory delta: {stats.get('memory_delta_mb', 0):.1f} MB")
    output_file = f"full_scale_parallel_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📄 Detailed results saved to: {output_file}")
    return results

if __name__ == "__main__":
    try:
        # Run main comparison test
        if len(sys.argv) > 1 and sys.argv[1] == "--full-scale":
            test_full_scale_parallel()
        else:
            results = test_parallel_vs_memory_optimized()
        # Run scaling test if requested
        if len(sys.argv) > 2 and sys.argv[2] == "--scaling":
            scaling_results = test_parallel_scaling()
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 