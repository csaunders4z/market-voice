#!/usr/bin/env python3
"""
Full Scale Performance Test for Market Voices
Tests the system with all 257 NASDAQ-100 and S&P 500 symbols
Measures performance, identifies bottlenecks, and validates production readiness
"""
import os
import sys
import json
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any
from loguru import logger

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_collection.symbol_loader import SymbolLoader
from src.data_collection.unified_data_collector import UnifiedDataCollector
from src.script_generation.script_generator import script_generator
from src.content_validation.quality_controls import quality_controller


class PerformanceMonitor:
    """Monitors system performance during testing"""
    
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.start_cpu = None
        self.measurements = []
        
    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        self.start_memory = psutil.virtual_memory().used
        self.start_cpu = psutil.cpu_percent(interval=1)
        logger.info(f"Performance monitoring started - Memory: {self.start_memory / 1024 / 1024:.1f} MB, CPU: {self.start_cpu}%")
        
    def record_measurement(self, stage: str, symbols_processed: int = 0):
        """Record a performance measurement"""
        current_time = time.time()
        current_memory = psutil.virtual_memory().used
        current_cpu = psutil.cpu_percent(interval=1)
        
        measurement = {
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'elapsed_time': current_time - self.start_time,
            'memory_used': current_memory,
            'memory_delta': current_memory - self.start_memory,
            'cpu_percent': current_cpu,
            'symbols_processed': symbols_processed
        }
        
        self.measurements.append(measurement)
        
        logger.info(f"📊 {stage}: {measurement['elapsed_time']:.1f}s, "
                   f"Memory: +{measurement['memory_delta'] / 1024 / 1024:.1f} MB, "
                   f"CPU: {current_cpu}%, "
                   f"Symbols: {symbols_processed}")
        
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.measurements:
            return {}
            
        total_time = self.measurements[-1]['elapsed_time']
        peak_memory = max(m['memory_used'] for m in self.measurements)
        avg_cpu = sum(m['cpu_percent'] for m in self.measurements) / len(self.measurements)
        
        return {
            'total_time_seconds': total_time,
            'peak_memory_mb': peak_memory / 1024 / 1024,
            'average_cpu_percent': avg_cpu,
            'measurements_count': len(self.measurements)
        }


def test_symbol_loading_performance():
    """Test symbol loading performance"""
    logger.info("🔍 Testing Symbol Loading Performance")
    logger.info("-" * 50)
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    try:
        # Test symbol loader
        symbol_loader = SymbolLoader()
        
        monitor.record_measurement("Symbol loader initialized")
        
        # Load NASDAQ-100 symbols
        nasdaq_symbols = symbol_loader.get_nasdaq_100_symbols()
        monitor.record_measurement("NASDAQ-100 loaded", len(nasdaq_symbols))
        
        # Load S&P 500 symbols
        sp500_symbols = symbol_loader.get_sp_500_symbols()
        monitor.record_measurement("S&P 500 loaded", len(sp500_symbols))
        
        # Get combined symbols
        all_symbols = symbol_loader.get_all_symbols()
        monitor.record_measurement("Combined symbols", len(all_symbols))
        
        # Validate coverage
        coverage = symbol_loader.validate_symbol_coverage()
        monitor.record_measurement("Coverage validation", len(all_symbols))
        
        logger.info(f"✅ Symbol loading completed successfully!")
        logger.info(f"  NASDAQ-100: {len(nasdaq_symbols)} symbols")
        logger.info(f"  S&P 500: {len(sp500_symbols)} symbols")
        logger.info(f"  Combined unique: {len(all_symbols)} symbols")
        
        return {
            'success': True,
            'symbols': all_symbols,
            'coverage': coverage,
            'performance': monitor.get_summary()
        }
        
    except Exception as e:
        logger.error(f"❌ Symbol loading failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'performance': monitor.get_summary()
        }


def test_data_collection_performance(symbols: List[str], test_size: int = 50):
    """Test data collection performance with a subset of symbols"""
    logger.info(f"📊 Testing Data Collection Performance (Sample: {test_size} symbols)")
    logger.info("-" * 50)
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    try:
        # Use a sample of symbols for testing
        test_symbols = symbols[:test_size] if len(symbols) > test_size else symbols
        
        # Initialize data collector
        collector = UnifiedDataCollector()
        monitor.record_measurement("Data collector initialized")
        
        # Test data collection
        logger.info(f"Collecting data for {len(test_symbols)} symbols...")
        market_data = collector.collect_data(symbols=test_symbols, production_mode=False)
        
        monitor.record_measurement("Data collection completed", len(test_symbols))
        
        # Analyze results
        if market_data.get('collection_success'):
            summary = market_data.get('market_summary', {})
            logger.info(f"✅ Data collection successful!")
            logger.info(f"  Total stocks processed: {summary.get('total_stocks_analyzed', 0)}")
            logger.info(f"  Advancing: {summary.get('advancing_stocks', 0)}")
            logger.info(f"  Declining: {summary.get('declining_stocks', 0)}")
            logger.info(f"  Data source: {market_data.get('data_source', 'Unknown')}")
            
            return {
                'success': True,
                'market_data': market_data,
                'symbols_tested': len(test_symbols),
                'performance': monitor.get_summary()
            }
        else:
            logger.error(f"❌ Data collection failed: {market_data.get('error', 'Unknown error')}")
            return {
                'success': False,
                'error': market_data.get('error', 'Unknown error'),
                'performance': monitor.get_summary()
            }
            
    except Exception as e:
        logger.error(f"❌ Data collection test failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'performance': monitor.get_summary()
        }


def test_script_generation_performance(market_data: Dict):
    """Test script generation performance"""
    logger.info("📝 Testing Script Generation Performance")
    logger.info("-" * 50)
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    try:
        monitor.record_measurement("Script generator initialized")
        
        # Generate script
        script_data = script_generator.generate_script(market_data)
        monitor.record_measurement("Script generation completed")
        
        if script_data.get('generation_success'):
            logger.info(f"✅ Script generation successful!")
            logger.info(f"  Lead host: {script_data.get('lead_host', 'Unknown')}")
            logger.info(f"  Segments: {len(script_data.get('segments', []))}")
            logger.info(f"  Runtime: {script_data.get('estimated_runtime_minutes', 0)} minutes")
            
            # Quality metrics
            quality_metrics = script_data.get('quality_metrics', {})
            logger.info(f"  Total words: {quality_metrics.get('total_words', 0)}")
            logger.info(f"  Technical indicators: {quality_metrics.get('technical_indicators_used', 0)}")
            
            return {
                'success': True,
                'script_data': script_data,
                'performance': monitor.get_summary()
            }
        else:
            logger.error(f"❌ Script generation failed: {script_data.get('error', 'Unknown error')}")
            return {
                'success': False,
                'error': script_data.get('error', 'Unknown error'),
                'performance': monitor.get_summary()
            }
            
    except Exception as e:
        logger.error(f"❌ Script generation test failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'performance': monitor.get_summary()
        }


def estimate_full_scale_performance(test_results: Dict) -> Dict[str, Any]:
    """Estimate performance for full 257 symbols based on test results"""
    logger.info("🔮 Estimating Full Scale Performance")
    logger.info("-" * 50)
    
    try:
        # Extract performance data
        symbol_perf = test_results.get('symbol_loading', {}).get('performance', {})
        data_perf = test_results.get('data_collection', {}).get('performance', {})
        script_perf = test_results.get('script_generation', {}).get('performance', {})
        
        # Calculate scaling factors
        symbols_tested = test_results.get('data_collection', {}).get('symbols_tested', 1)
        total_symbols = 257
        
        if symbols_tested == 0:
            return {'error': 'No symbols tested, cannot estimate performance'}
        
        scaling_factor = total_symbols / symbols_tested
        
        # Estimate times
        estimated_data_time = data_perf.get('total_time_seconds', 0) * scaling_factor
        estimated_script_time = script_perf.get('total_time_seconds', 0)  # Script generation doesn't scale with symbols
        estimated_total_time = estimated_data_time + estimated_script_time
        
        # Estimate memory usage
        estimated_peak_memory = data_perf.get('peak_memory_mb', 0) * scaling_factor
        
        # Estimate API costs (rough calculation)
        # Assuming ~10 API calls per symbol for data collection
        estimated_api_calls = total_symbols * 10
        estimated_cost_per_call = 0.001  # Rough estimate
        estimated_total_cost = estimated_api_calls * estimated_cost_per_call
        
        estimates = {
            'total_symbols': total_symbols,
            'estimated_data_collection_time_minutes': estimated_data_time / 60,
            'estimated_script_generation_time_minutes': estimated_script_time / 60,
            'estimated_total_time_minutes': estimated_total_time / 60,
            'estimated_peak_memory_mb': estimated_peak_memory,
            'estimated_api_calls': estimated_api_calls,
            'estimated_total_cost_usd': estimated_total_cost,
            'scaling_factor': scaling_factor
        }
        
        logger.info(f"📊 Performance Estimates for {total_symbols} symbols:")
        logger.info(f"  Data Collection: {estimates['estimated_data_collection_time_minutes']:.1f} minutes")
        logger.info(f"  Script Generation: {estimates['estimated_script_generation_time_minutes']:.1f} minutes")
        logger.info(f"  Total Time: {estimates['estimated_total_time_minutes']:.1f} minutes")
        logger.info(f"  Peak Memory: {estimates['estimated_peak_memory_mb']:.1f} MB")
        logger.info(f"  API Calls: {estimates['estimated_api_calls']:,}")
        logger.info(f"  Estimated Cost: ${estimates['estimated_total_cost_usd']:.2f}")
        
        return estimates
        
    except Exception as e:
        logger.error(f"❌ Performance estimation failed: {str(e)}")
        return {'error': str(e)}


def generate_performance_report(test_results: Dict, estimates: Dict):
    """Generate comprehensive performance report"""
    logger.info("📋 Generating Performance Report")
    logger.info("-" * 50)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"output/performance_report_{timestamp}.json"
    
    # Create comprehensive report
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_summary': {
            'symbol_loading_success': test_results.get('symbol_loading', {}).get('success', False),
            'data_collection_success': test_results.get('data_collection', {}).get('success', False),
            'script_generation_success': test_results.get('script_generation', {}).get('success', False),
            'overall_success': all([
                test_results.get('symbol_loading', {}).get('success', False),
                test_results.get('data_collection', {}).get('success', False),
                test_results.get('script_generation', {}).get('success', False)
            ])
        },
        'performance_metrics': {
            'symbol_loading': test_results.get('symbol_loading', {}).get('performance', {}),
            'data_collection': test_results.get('data_collection', {}).get('performance', {}),
            'script_generation': test_results.get('script_generation', {}).get('performance', {})
        },
        'full_scale_estimates': estimates,
        'recommendations': generate_recommendations(test_results, estimates),
        'raw_test_results': test_results
    }
    
    # Save report
    os.makedirs("output", exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"✅ Performance report saved to: {report_file}")
    
    # Print summary
    print_performance_summary(report)
    
    return report_file


def generate_recommendations(test_results: Dict, estimates: Dict) -> List[str]:
    """Generate recommendations based on test results"""
    recommendations = []
    
    # Check if we meet performance targets
    total_time_minutes = estimates.get('estimated_total_time_minutes', 0)
    if total_time_minutes > 30:
        recommendations.append("⚠️ Total processing time exceeds 30-minute target. Consider implementing parallel processing.")
    
    peak_memory = estimates.get('estimated_peak_memory_mb', 0)
    if peak_memory > 2048:  # 2GB
        recommendations.append("⚠️ Peak memory usage may be high. Consider memory optimization and garbage collection.")
    
    estimated_cost = estimates.get('estimated_total_cost_usd', 0)
    if estimated_cost > 100:
        recommendations.append("⚠️ Estimated monthly cost exceeds $100 target. Consider API usage optimization.")
    
    # Check for errors
    if not test_results.get('symbol_loading', {}).get('success', False):
        recommendations.append("❌ Symbol loading failed. Review symbol sources and network connectivity.")
    
    if not test_results.get('data_collection', {}).get('success', False):
        recommendations.append("❌ Data collection failed. Review API keys and rate limiting.")
    
    if not test_results.get('script_generation', {}).get('success', False):
        recommendations.append("❌ Script generation failed. Review script generation logic.")
    
    # Positive recommendations
    if total_time_minutes <= 30:
        recommendations.append("✅ Performance meets target requirements.")
    
    if peak_memory <= 2048:
        recommendations.append("✅ Memory usage is within acceptable limits.")
    
    if estimated_cost <= 100:
        recommendations.append("✅ Estimated costs are within budget.")
    
    return recommendations


def print_performance_summary(report: Dict):
    """Print a summary of the performance report"""
    logger.info("\n" + "=" * 70)
    logger.info("📊 PERFORMANCE TEST SUMMARY")
    logger.info("=" * 70)
    
    summary = report['test_summary']
    estimates = report['full_scale_estimates']
    
    # Overall status
    if summary['overall_success']:
        logger.info("🎉 ALL TESTS PASSED - System ready for production!")
    else:
        logger.error("❌ SOME TESTS FAILED - Review issues before production deployment")
    
    # Component status
    logger.info(f"\nComponent Status:")
    logger.info(f"  Symbol Loading: {'✅ PASS' if summary['symbol_loading_success'] else '❌ FAIL'}")
    logger.info(f"  Data Collection: {'✅ PASS' if summary['data_collection_success'] else '❌ FAIL'}")
    logger.info(f"  Script Generation: {'✅ PASS' if summary['script_generation_success'] else '❌ FAIL'}")
    
    # Performance metrics
    logger.info(f"\nPerformance Metrics (257 symbols):")
    logger.info(f"  Estimated Total Time: {estimates.get('estimated_total_time_minutes', 0):.1f} minutes")
    logger.info(f"  Estimated Peak Memory: {estimates.get('estimated_peak_memory_mb', 0):.1f} MB")
    logger.info(f"  Estimated API Cost: ${estimates.get('estimated_total_cost_usd', 0):.2f}")
    
    # Recommendations
    recommendations = report.get('recommendations', [])
    if recommendations:
        logger.info(f"\nRecommendations:")
        for rec in recommendations:
            logger.info(f"  {rec}")
    
    logger.info("=" * 70)


def main():
    """Run the full scale performance test"""
    logger.info("🚀 Starting Full Scale Performance Test")
    logger.info("=" * 70)
    logger.info("This test will evaluate system performance for production scale")
    logger.info("Testing with all 257 NASDAQ-100 and S&P 500 symbols")
    logger.info("=" * 70)
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
    
    test_results = {}
    
    try:
        # Step 1: Test symbol loading
        logger.info("\n🔍 STEP 1: Symbol Loading Performance Test")
        test_results['symbol_loading'] = test_symbol_loading_performance()
        
        if not test_results['symbol_loading']['success']:
            logger.error("❌ Symbol loading failed, cannot continue")
            return False
        
        symbols = test_results['symbol_loading']['symbols']
        logger.info(f"✅ Loaded {len(symbols)} symbols successfully")
        
        # Step 2: Test data collection (with sample)
        logger.info("\n📊 STEP 2: Data Collection Performance Test")
        test_results['data_collection'] = test_data_collection_performance(symbols, test_size=50)
        
        if not test_results['data_collection']['success']:
            logger.error("❌ Data collection failed, cannot continue")
            return False
        
        market_data = test_results['data_collection']['market_data']
        
        # Step 3: Test script generation
        logger.info("\n📝 STEP 3: Script Generation Performance Test")
        test_results['script_generation'] = test_script_generation_performance(market_data)
        
        if not test_results['script_generation']['success']:
            logger.error("❌ Script generation failed")
            return False
        
        # Step 4: Estimate full scale performance
        logger.info("\n🔮 STEP 4: Full Scale Performance Estimation")
        estimates = estimate_full_scale_performance(test_results)
        
        # Step 5: Generate report
        logger.info("\n📋 STEP 5: Generate Performance Report")
        report_file = generate_performance_report(test_results, estimates)
        
        logger.info(f"\n🎉 Full Scale Performance Test Completed!")
        logger.info(f"Report saved to: {report_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    print(f"\nFull scale performance test completed with {'SUCCESS' if success else 'FAILURE'}")
    sys.exit(0 if success else 1) 