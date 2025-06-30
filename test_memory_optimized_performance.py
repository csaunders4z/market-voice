#!/usr/bin/env python3
"""
Memory-Optimized Performance Test for Market Voices
Compares memory usage between original and optimized data collectors
"""
import os
import sys
import json
import time
import psutil
import gc
from datetime import datetime
from typing import Dict, List, Any
from loguru import logger

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_collection.symbol_loader import SymbolLoader
from src.data_collection.unified_data_collector import UnifiedDataCollector
from src.data_collection.memory_optimized_collector import MemoryOptimizedCollector
from src.script_generation.script_generator import script_generator


class MemoryPerformanceMonitor:
    """Monitors memory performance during testing"""
    
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.measurements = []
        self.process = psutil.Process()
        
    def start_monitoring(self):
        """Start memory monitoring"""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024
        logger.info(f"Memory monitoring started - Initial: {self.start_memory:.1f} MB")
        
    def record_measurement(self, stage: str, symbols_processed: int = 0):
        """Record a memory measurement"""
        current_time = time.time()
        current_memory = self.process.memory_info().rss / 1024 / 1024
        memory_delta = current_memory - self.start_memory
        
        measurement = {
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'elapsed_time': current_time - self.start_time,
            'memory_mb': current_memory,
            'memory_delta_mb': memory_delta,
            'symbols_processed': symbols_processed
        }
        
        self.measurements.append(measurement)
        
        logger.info(f"📊 {stage}: {measurement['elapsed_time']:.1f}s, "
                   f"Memory: {current_memory:.1f} MB (delta: {memory_delta:+.1f} MB), "
                   f"Symbols: {symbols_processed}")
        
    def get_summary(self) -> Dict[str, Any]:
        """Get memory performance summary"""
        if not self.measurements:
            return {}
            
        total_time = self.measurements[-1]['elapsed_time']
        peak_memory = max(m['memory_mb'] for m in self.measurements)
        final_memory = self.measurements[-1]['memory_mb']
        memory_growth = final_memory - self.start_memory
        
        return {
            'total_time_seconds': total_time,
            'peak_memory_mb': peak_memory,
            'final_memory_mb': final_memory,
            'memory_growth_mb': memory_growth,
            'measurements_count': len(self.measurements)
        }


def test_original_collector_memory(symbols: List[str], test_size: int = 30):
    """Test original collector memory usage"""
    logger.info("🔍 Testing Original Collector Memory Usage")
    logger.info("-" * 50)
    
    monitor = MemoryPerformanceMonitor()
    monitor.start_monitoring()
    
    try:
        # Force garbage collection before test
        gc.collect()
        monitor.record_measurement("Garbage collection before test")
        
        # Use a sample of symbols for testing
        test_symbols = symbols[:test_size] if len(symbols) > test_size else symbols
        
        # Initialize original collector
        collector = UnifiedDataCollector()
        monitor.record_measurement("Original collector initialized")
        
        # Test data collection
        logger.info(f"Collecting data for {len(test_symbols)} symbols with original collector...")
        market_data = collector.collect_data(symbols=test_symbols, production_mode=False)
        
        monitor.record_measurement("Original collection completed", len(test_symbols))
        
        # Analyze results
        if market_data.get('collection_success'):
            summary = market_data.get('market_summary', {})
            logger.info(f"✅ Original collection successful!")
            logger.info(f"  Total stocks processed: {summary.get('total_stocks_analyzed', 0)}")
            logger.info(f"  Data source: {market_data.get('data_source', 'Unknown')}")
            
            return {
                'success': True,
                'market_data': market_data,
                'symbols_tested': len(test_symbols),
                'performance': monitor.get_summary()
            }
        else:
            logger.error(f"❌ Original collection failed: {market_data.get('error', 'Unknown error')}")
            return {
                'success': False,
                'error': market_data.get('error', 'Unknown error'),
                'performance': monitor.get_summary()
            }
            
    except Exception as e:
        logger.error(f"❌ Original collection test failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'performance': monitor.get_summary()
        }
    finally:
        # Force garbage collection after test
        gc.collect()


def test_optimized_collector_memory(symbols: List[str], test_size: int = 30):
    """Test optimized collector memory usage"""
    logger.info("🚀 Testing Memory-Optimized Collector Memory Usage")
    logger.info("-" * 50)
    
    monitor = MemoryPerformanceMonitor()
    monitor.start_monitoring()
    
    try:
        # Force garbage collection before test
        gc.collect()
        monitor.record_measurement("Garbage collection before test")
        
        # Use a sample of symbols for testing
        test_symbols = symbols[:test_size] if len(symbols) > test_size else symbols
        
        # Initialize optimized collector
        collector = MemoryOptimizedCollector()
        monitor.record_measurement("Optimized collector initialized")
        
        # Test data collection
        logger.info(f"Collecting data for {len(test_symbols)} symbols with optimized collector...")
        market_data = collector.collect_data_optimized(symbols=test_symbols, production_mode=False)
        
        monitor.record_measurement("Optimized collection completed", len(test_symbols))
        
        # Analyze results
        if market_data.get('collection_success'):
            summary = market_data.get('market_summary', {})
            logger.info(f"✅ Optimized collection successful!")
            logger.info(f"  Total stocks processed: {summary.get('total_stocks_analyzed', 0)}")
            logger.info(f"  Data source: {market_data.get('data_source', 'Unknown')}")
            
            return {
                'success': True,
                'market_data': market_data,
                'symbols_tested': len(test_symbols),
                'performance': monitor.get_summary()
            }
        else:
            logger.error(f"❌ Optimized collection failed: {market_data.get('error', 'Unknown error')}")
            return {
                'success': False,
                'error': market_data.get('error', 'Unknown error'),
                'performance': monitor.get_summary()
            }
            
    except Exception as e:
        logger.error(f"❌ Optimized collection test failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'performance': monitor.get_summary()
        }
    finally:
        # Force garbage collection after test
        gc.collect()


def compare_memory_performance(original_results: Dict, optimized_results: Dict) -> Dict[str, Any]:
    """Compare memory performance between original and optimized collectors"""
    logger.info("📊 Comparing Memory Performance")
    logger.info("-" * 50)
    
    original_perf = original_results.get('performance', {})
    optimized_perf = optimized_results.get('performance', {})
    
    # Calculate improvements
    memory_reduction = original_perf.get('peak_memory_mb', 0) - optimized_perf.get('peak_memory_mb', 0)
    memory_reduction_pct = (memory_reduction / original_perf.get('peak_memory_mb', 1)) * 100 if original_perf.get('peak_memory_mb', 0) > 0 else 0
    
    time_difference = optimized_perf.get('total_time_seconds', 0) - original_perf.get('total_time_seconds', 0)
    time_difference_pct = (time_difference / original_perf.get('total_time_seconds', 1)) * 100 if original_perf.get('total_time_seconds', 0) > 0 else 0
    
    comparison = {
        'original_performance': original_perf,
        'optimized_performance': optimized_perf,
        'improvements': {
            'memory_reduction_mb': memory_reduction,
            'memory_reduction_percent': memory_reduction_pct,
            'time_difference_seconds': time_difference,
            'time_difference_percent': time_difference_pct
        },
        'recommendations': []
    }
    
    # Generate recommendations
    if memory_reduction > 0:
        comparison['recommendations'].append(f"✅ Memory usage reduced by {memory_reduction:.1f} MB ({memory_reduction_pct:.1f}%)")
    else:
        comparison['recommendations'].append(f"⚠️ Memory usage increased by {abs(memory_reduction):.1f} MB")
    
    if time_difference < 0:
        comparison['recommendations'].append(f"✅ Processing time reduced by {abs(time_difference):.1f} seconds ({abs(time_difference_pct):.1f}%)")
    else:
        comparison['recommendations'].append(f"⚠️ Processing time increased by {time_difference:.1f} seconds")
    
    # Check if we meet memory targets
    optimized_peak_mb = optimized_perf.get('peak_memory_mb', 0)
    if optimized_peak_mb <= 2048:  # 2GB target
        comparison['recommendations'].append("✅ Peak memory usage within 2GB target")
    else:
        comparison['recommendations'].append(f"⚠️ Peak memory usage ({optimized_peak_mb:.1f} MB) exceeds 2GB target")
    
    logger.info(f"📊 Memory Performance Comparison:")
    logger.info(f"  Original Peak Memory: {original_perf.get('peak_memory_mb', 0):.1f} MB")
    logger.info(f"  Optimized Peak Memory: {optimized_perf.get('peak_memory_mb', 0):.1f} MB")
    logger.info(f"  Memory Reduction: {memory_reduction:.1f} MB ({memory_reduction_pct:.1f}%)")
    logger.info(f"  Original Time: {original_perf.get('total_time_seconds', 0):.1f} seconds")
    logger.info(f"  Optimized Time: {optimized_perf.get('total_time_seconds', 0):.1f} seconds")
    logger.info(f"  Time Difference: {time_difference:+.1f} seconds ({time_difference_pct:+.1f}%)")
    
    return comparison


def estimate_full_scale_memory_impact(comparison: Dict, test_size: int = 30) -> Dict[str, Any]:
    """Estimate full-scale memory impact based on comparison results"""
    logger.info("🔮 Estimating Full-Scale Memory Impact")
    logger.info("-" * 50)
    
    total_symbols = 257
    scaling_factor = total_symbols / test_size
    
    original_perf = comparison['original_performance']
    optimized_perf = comparison['optimized_performance']
    
    # Estimate full-scale memory usage
    original_full_scale = original_perf.get('peak_memory_mb', 0) * scaling_factor
    optimized_full_scale = optimized_perf.get('peak_memory_mb', 0) * scaling_factor
    
    # Estimate full-scale time
    original_full_time = original_perf.get('total_time_seconds', 0) * scaling_factor
    optimized_full_time = optimized_perf.get('total_time_seconds', 0) * scaling_factor
    
    estimates = {
        'test_symbols': test_size,
        'full_scale_symbols': total_symbols,
        'scaling_factor': scaling_factor,
        'original_full_scale': {
            'peak_memory_mb': original_full_scale,
            'total_time_minutes': original_full_time / 60
        },
        'optimized_full_scale': {
            'peak_memory_mb': optimized_full_scale,
            'total_time_minutes': optimized_full_time / 60
        },
        'improvements_full_scale': {
            'memory_reduction_mb': original_full_scale - optimized_full_scale,
            'memory_reduction_percent': ((original_full_scale - optimized_full_scale) / original_full_scale) * 100 if original_full_scale > 0 else 0,
            'time_reduction_minutes': (original_full_time - optimized_full_time) / 60,
            'time_reduction_percent': ((original_full_time - optimized_full_time) / original_full_time) * 100 if original_full_time > 0 else 0
        }
    }
    
    logger.info(f"📊 Full-Scale Estimates (257 symbols):")
    logger.info(f"  Original Peak Memory: {original_full_scale:.1f} MB")
    logger.info(f"  Optimized Peak Memory: {optimized_full_scale:.1f} MB")
    logger.info(f"  Memory Reduction: {estimates['improvements_full_scale']['memory_reduction_mb']:.1f} MB ({estimates['improvements_full_scale']['memory_reduction_percent']:.1f}%)")
    logger.info(f"  Original Time: {estimates['original_full_scale']['total_time_minutes']:.1f} minutes")
    logger.info(f"  Optimized Time: {estimates['optimized_full_scale']['total_time_minutes']:.1f} minutes")
    logger.info(f"  Time Reduction: {estimates['improvements_full_scale']['time_reduction_minutes']:.1f} minutes ({estimates['improvements_full_scale']['time_reduction_percent']:.1f}%)")
    
    return estimates


def generate_memory_optimization_report(original_results: Dict, optimized_results: Dict, comparison: Dict, estimates: Dict):
    """Generate comprehensive memory optimization report"""
    logger.info("📋 Generating Memory Optimization Report")
    logger.info("-" * 50)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"output/memory_optimization_report_{timestamp}.json"
    
    # Create comprehensive report
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_summary': {
            'original_collector_success': original_results.get('success', False),
            'optimized_collector_success': optimized_results.get('success', False),
            'both_successful': original_results.get('success', False) and optimized_results.get('success', False)
        },
        'performance_comparison': comparison,
        'full_scale_estimates': estimates,
        'recommendations': comparison.get('recommendations', []),
        'raw_test_results': {
            'original': original_results,
            'optimized': optimized_results
        }
    }
    
    # Save report
    os.makedirs("output", exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"✅ Memory optimization report saved to: {report_file}")
    
    # Print summary
    print_memory_optimization_summary(report)
    
    return report_file


def print_memory_optimization_summary(report: Dict):
    """Print a summary of the memory optimization report"""
    logger.info("\n" + "=" * 70)
    logger.info("📊 MEMORY OPTIMIZATION SUMMARY")
    logger.info("=" * 70)
    
    summary = report['test_summary']
    comparison = report['performance_comparison']
    estimates = report['full_scale_estimates']
    
    # Overall status
    if summary['both_successful']:
        logger.info("🎉 MEMORY OPTIMIZATION TEST COMPLETED SUCCESSFULLY!")
    else:
        logger.error("❌ SOME TESTS FAILED - Review issues before proceeding")
    
    # Component status
    logger.info(f"\nComponent Status:")
    logger.info(f"  Original Collector: {'✅ PASS' if summary['original_collector_success'] else '❌ FAIL'}")
    logger.info(f"  Optimized Collector: {'✅ PASS' if summary['optimized_collector_success'] else '❌ FAIL'}")
    
    # Performance improvements
    improvements = comparison.get('improvements', {})
    logger.info(f"\nMemory Performance Improvements:")
    logger.info(f"  Memory Reduction: {improvements.get('memory_reduction_mb', 0):.1f} MB ({improvements.get('memory_reduction_percent', 0):.1f}%)")
    logger.info(f"  Time Impact: {improvements.get('time_difference_seconds', 0):+.1f} seconds ({improvements.get('time_difference_percent', 0):+.1f}%)")
    
    # Full-scale estimates
    full_scale_improvements = estimates.get('improvements_full_scale', {})
    logger.info(f"\nFull-Scale Impact (257 symbols):")
    logger.info(f"  Memory Reduction: {full_scale_improvements.get('memory_reduction_mb', 0):.1f} MB ({full_scale_improvements.get('memory_reduction_percent', 0):.1f}%)")
    logger.info(f"  Time Reduction: {full_scale_improvements.get('time_reduction_minutes', 0):.1f} minutes ({full_scale_improvements.get('time_reduction_percent', 0):.1f}%)")
    
    # Recommendations
    recommendations = report.get('recommendations', [])
    if recommendations:
        logger.info(f"\nRecommendations:")
        for rec in recommendations:
            logger.info(f"  {rec}")
    
    logger.info("=" * 70)


def main():
    """Run the memory optimization performance test"""
    logger.info("🚀 Starting Memory Optimization Performance Test")
    logger.info("=" * 70)
    logger.info("This test will compare memory usage between original and optimized collectors")
    logger.info("=" * 70)
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
    
    try:
        # Step 1: Load symbols
        logger.info("\n🔍 STEP 1: Loading Symbols")
        symbol_loader = SymbolLoader()
        symbols = symbol_loader.get_all_symbols()
        logger.info(f"✅ Loaded {len(symbols)} symbols")
        
        # Step 2: Test original collector
        logger.info("\n📊 STEP 2: Testing Original Collector")
        original_results = test_original_collector_memory(symbols, test_size=30)
        
        if not original_results['success']:
            logger.error("❌ Original collector test failed, cannot continue")
            return False
        
        # Step 3: Test optimized collector
        logger.info("\n🚀 STEP 3: Testing Memory-Optimized Collector")
        optimized_results = test_optimized_collector_memory(symbols, test_size=30)
        
        if not optimized_results['success']:
            logger.error("❌ Optimized collector test failed")
            return False
        
        # Step 4: Compare performance
        logger.info("\n📊 STEP 4: Comparing Performance")
        comparison = compare_memory_performance(original_results, optimized_results)
        
        # Step 5: Estimate full-scale impact
        logger.info("\n🔮 STEP 5: Estimating Full-Scale Impact")
        estimates = estimate_full_scale_memory_impact(comparison, test_size=30)
        
        # Step 6: Generate report
        logger.info("\n📋 STEP 6: Generate Memory Optimization Report")
        report_file = generate_memory_optimization_report(original_results, optimized_results, comparison, estimates)
        
        logger.info(f"\n🎉 Memory Optimization Performance Test Completed!")
        logger.info(f"Report saved to: {report_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Memory optimization test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    print(f"\nMemory optimization performance test completed with {'SUCCESS' if success else 'FAILURE'}")
    sys.exit(0 if success else 1) 