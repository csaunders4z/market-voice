"""
Parallel Data Collector for Market Voices
High-performance concurrent data collection with memory optimization and rate limiting
"""
import time
import gc
import asyncio
import aiohttp
import concurrent.futures
from typing import Dict, List, Optional, Tuple, Any, Iterator, Generator
from datetime import datetime
from loguru import logger
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import dataclass
from queue import Queue
import signal
import sys

from ..config.settings import get_settings
from ..utils.rate_limiter import RateLimiter
from ..utils.error_recovery import (
    error_recovery_manager, 
    with_error_recovery, 
    with_graceful_degradation,
    CircuitBreakerConfig,
    ErrorRecoveryManager
)


@dataclass
class CollectionTask:
    """Task for parallel data collection"""
    symbol: str
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3


class ParallelCollector:
    """High-performance parallel data collector with memory optimization"""
    
    def __init__(self, max_workers: int = 10, batch_size: int = 20):
        self.settings = get_settings()
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.rate_limiter = RateLimiter()  # Fixed: no parameters needed
        self.memory_threshold = 2.0  # 2GB memory threshold
        
        # Error recovery setup
        self.error_manager = error_recovery_manager
        self.yahoo_circuit_breaker = self.error_manager.get_or_create_circuit_breaker(
            "yahoo_finance",
            CircuitBreakerConfig(failure_threshold=10, recovery_timeout=120)
        )
        
        self.collection_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'retries': 0,
            'start_time': None,
            'end_time': None,
            'errors_handled': 0,
            'circuit_breaker_trips': 0
        }
        
        # Thread-safe collections
        self._lock = threading.Lock()
        self._collected_data = []
        self._failed_symbols = []
        
        # Graceful shutdown handling
        self._shutdown_event = threading.Event()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info("Received shutdown signal, stopping collection...")
        self._shutdown_event.set()
    
    def _check_memory_usage(self) -> float:
        """Check current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            return memory_mb
        except ImportError:
            logger.warning("psutil not available, cannot monitor memory usage")
            return 0.0
    
    def _should_stop_collection(self) -> bool:
        """Check if collection should stop due to memory or shutdown"""
        if self._shutdown_event.is_set():
            return True
        
        memory_usage = self._check_memory_usage()
        if memory_usage > self.memory_threshold * 1024:  # Convert GB to MB
            logger.warning(f"Memory usage {memory_usage:.1f} MB exceeds threshold {self.memory_threshold * 1024:.1f} MB")
            return True
        
        return False
    
    def _minimal_stock_data(self, symbol: str, ticker: yf.Ticker) -> Optional[Dict]:
        """Extract minimal stock data to reduce memory usage"""
        try:
            # Get current price and basic info
            info = ticker.info
            
            current_price = info.get('currentPrice', 0)
            previous_close = info.get('previousClose', current_price)
            
            if current_price == 0 or previous_close == 0:
                return None
            
            price_change = current_price - previous_close
            percent_change = (price_change / previous_close) * 100 if previous_close > 0 else 0
            
            # Get volume data
            current_volume = info.get('volume', 0)
            average_volume = info.get('averageVolume', current_volume)
            volume_ratio = current_volume / average_volume if average_volume > 0 else 1.0
            
            # Get market cap
            market_cap = info.get('marketCap', 0)
            
            return {
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'previous_price': round(previous_close, 2),
                'price_change': round(price_change, 2),
                'percent_change': round(percent_change, 2),
                'current_volume': current_volume,
                'average_volume': average_volume,
                'volume_ratio': round(volume_ratio, 2),
                'market_cap': market_cap,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Failed to fetch minimal data for {symbol}: {str(e)}")
            return None
    
    def _process_symbol(self, task: CollectionTask) -> Optional[Dict]:
        """Process a single symbol with enhanced error recovery"""
        if self._should_stop_collection():
            return None
        
        try:
            # Use circuit breaker for Yahoo Finance API calls
            def fetch_yahoo_data():
                # Rate limiting using the existing RateLimiter
                self.rate_limiter._wait_for_rate_limit("yahoo", 0.1)  # 0.1s delay between requests
                
                # Fetch data
                ticker = yf.Ticker(task.symbol)
                stock_data = self._minimal_stock_data(task.symbol, ticker)
                return stock_data
            
            # Execute with circuit breaker protection
            stock_data = self.yahoo_circuit_breaker.call(fetch_yahoo_data)
            
            if stock_data:
                with self._lock:
                    self.collection_stats['successful'] += 1
                return stock_data
            else:
                # Enhanced retry logic with error classification
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    with self._lock:
                        self.collection_stats['retries'] += 1
                    logger.info(f"Retrying {task.symbol} (attempt {task.retry_count}/{task.max_retries})")
                    
                    # Exponential backoff for retries
                    delay = min(2 ** task.retry_count, 10)  # Cap at 10 seconds
                    time.sleep(delay)
                    return self._process_symbol(task)
                else:
                    with self._lock:
                        self.collection_stats['failed'] += 1
                        self._failed_symbols.append(task.symbol)
                    logger.warning(f"Failed to collect data for {task.symbol} after {task.max_retries} attempts")
                    return None
                    
        except Exception as e:
            # Enhanced error handling with classification and recovery
            error_info = self.error_manager.handle_error(e, {
                'symbol': task.symbol,
                'retry_count': task.retry_count,
                'function': '_process_symbol'
            })
            
            with self._lock:
                self.collection_stats['errors_handled'] += 1
                
                # Check if circuit breaker was triggered
                if self.yahoo_circuit_breaker.state.value == 'open':
                    self.collection_stats['circuit_breaker_trips'] += 1
            
            # Handle specific error types
            if error_info.error_type.value == 'rate_limit':
                # Rate limit errors - use exponential backoff
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    delay = min(2 ** task.retry_count, 30)  # Longer delay for rate limits
                    logger.info(f"Rate limit hit for {task.symbol}, retrying in {delay}s")
                    time.sleep(delay)
                    return self._process_symbol(task)
            
            elif error_info.error_type.value == 'network':
                # Network errors - retry with shorter delays
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    logger.info(f"Network error for {task.symbol}, retrying...")
                    time.sleep(2)
                    return self._process_symbol(task)
            
            # For other errors, mark as failed
            with self._lock:
                self.collection_stats['failed'] += 1
                self._failed_symbols.append(task.symbol)
            
            logger.warning(f"Error processing {task.symbol}: {error_info.message} (type: {error_info.error_type.value})")
            return None
            
        finally:
            # Clear ticker reference
            if 'ticker' in locals():
                del ticker
    
    def _process_batch(self, batch: List[CollectionTask]) -> List[Dict]:
        """Process a batch of symbols using thread pool"""
        batch_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._process_symbol, task): task 
                for task in batch
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                if self._should_stop_collection():
                    break
                
                task = future_to_task[future]
                try:
                    result = future.result()
                    if result:
                        batch_results.append(result)
                        with self._lock:
                            self._collected_data.append(result)
                except Exception as e:
                    logger.error(f"Task for {task.symbol} generated an exception: {str(e)}")
                    with self._lock:
                        self.collection_stats['failed'] += 1
                        self._failed_symbols.append(task.symbol)
        
        return batch_results
    
    def _create_tasks(self, symbols: List[str]) -> List[CollectionTask]:
        """Create collection tasks from symbols"""
        tasks = []
        
        # Prioritize symbols (you can implement custom prioritization logic here)
        for i, symbol in enumerate(symbols):
            priority = 1  # Default priority
            if symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']:  # High priority symbols
                priority = 10
            elif symbol in ['META', 'TSLA', 'BRK.B', 'LLY', 'UNH']:  # Medium priority
                priority = 5
            
            task = CollectionTask(symbol=symbol, priority=priority)
            tasks.append(task)
        
        # Sort by priority (highest first)
        tasks.sort(key=lambda x: x.priority, reverse=True)
        return tasks
    
    def _stream_tasks(self, tasks: List[CollectionTask]) -> Generator[List[CollectionTask], None, None]:
        """Stream tasks in batches"""
        for i in range(0, len(tasks), self.batch_size):
            batch = tasks[i:i + self.batch_size]
            yield batch
    
    def collect_data_parallel(self, symbols: List[str] = None, production_mode: bool = True) -> Dict:
        """Collect data using parallel processing"""
        logger.info(f"Starting parallel data collection with {self.max_workers} workers")
        
        # Reset stats
        self.collection_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'retries': 0,
            'start_time': datetime.now(),
            'end_time': None,
            'errors_handled': 0,
            'circuit_breaker_trips': 0
        }
        
        self._collected_data = []
        self._failed_symbols = []
        
        # Use provided symbols or get from settings
        if symbols is None:
            symbols = self.settings.symbols[:self.settings.max_symbols_per_collection]
        
        if not isinstance(symbols, list):
            symbols = []
        
        logger.info(f"Collecting data for {len(symbols)} symbols using parallel processing")
        
        # Initial memory check
        initial_memory = self._check_memory_usage()
        logger.info(f"Initial memory usage: {initial_memory:.1f} MB")
        
        # Force initial garbage collection
        gc.collect()
        
        try:
            # Create tasks
            tasks = self._create_tasks(symbols)
            self.collection_stats['total_processed'] = len(tasks)
            
            # Process in batches
            batch_count = 0
            for batch in self._stream_tasks(tasks):
                if self._should_stop_collection():
                    logger.warning("Collection stopped due to memory threshold or shutdown signal")
                    break
                
                batch_count += 1
                logger.info(f"Processing batch {batch_count} of {len(batch)} symbols")
                
                # Process batch
                batch_results = self._process_batch(batch)
                
                # Memory check after each batch
                current_memory = self._check_memory_usage()
                logger.info(f"Batch {batch_count} completed: {len(batch_results)} successful, memory: {current_memory:.1f} MB")
                
                # Force garbage collection after each batch
                gc.collect()
                
                # Brief pause between batches to prevent overwhelming APIs
                time.sleep(0.1)
            
            # Final memory check
            final_memory = self._check_memory_usage()
            logger.info(f"Final memory usage: {final_memory:.1f} MB (delta: {final_memory - initial_memory:.1f} MB)")
            
            # Calculate performance metrics
            self.collection_stats['end_time'] = datetime.now()
            duration = (self.collection_stats['end_time'] - self.collection_stats['start_time']).total_seconds()
            
            success_rate = (self.collection_stats['successful'] / self.collection_stats['total_processed']) * 100 if self.collection_stats['total_processed'] > 0 else 0
            
            logger.info(f"Parallel collection completed:")
            logger.info(f"  Duration: {duration:.2f} seconds")
            logger.info(f"  Success rate: {success_rate:.1f}%")
            logger.info(f"  Successful: {self.collection_stats['successful']}")
            logger.info(f"  Failed: {self.collection_stats['failed']}")
            logger.info(f"  Retries: {self.collection_stats['retries']}")
            logger.info(f"  Errors handled: {self.collection_stats['errors_handled']}")
            logger.info(f"  Circuit breaker trips: {self.collection_stats['circuit_breaker_trips']}")
            
            # Log error recovery summary
            error_summary = self.error_manager.get_error_summary()
            if error_summary['total_errors'] > 0:
                logger.info(f"Error recovery summary: {error_summary}")
            
            if self._collected_data:
                # Create market summary
                market_summary = self._create_market_summary(self._collected_data)
                
                # Get top winners and losers
                sorted_data = sorted(self._collected_data, key=lambda x: x.get('percent_change', 0), reverse=True)
                winners = [stock for stock in sorted_data if stock.get('percent_change', 0) > 0][:5]
                losers = [stock for stock in sorted_data if stock.get('percent_change', 0) < 0][:5]
                
                result = {
                    'market_summary': market_summary,
                    'winners': winners,
                    'losers': losers,
                    'all_data': self._collected_data,
                    'collection_success': True,
                    'data_source': 'Yahoo Finance (Parallel)',
                    'timestamp': datetime.now().isoformat(),
                    'performance_stats': {
                        'duration_seconds': duration,
                        'success_rate_percent': success_rate,
                        'symbols_processed': self.collection_stats['total_processed'],
                        'symbols_successful': self.collection_stats['successful'],
                        'symbols_failed': self.collection_stats['failed'],
                        'retry_count': self.collection_stats['retries'],
                        'memory_usage_mb': final_memory,
                        'memory_delta_mb': final_memory - initial_memory,
                        'errors_handled': self.collection_stats['errors_handled'],
                        'circuit_breaker_trips': self.collection_stats['circuit_breaker_trips']
                    },
                    'error_recovery': self.error_manager.get_error_summary(),
                    'circuit_breaker_status': self.yahoo_circuit_breaker.get_status()
                }
                
                logger.info(f"Parallel data collection successful using Yahoo Finance (Parallel)")
                return result
            
            # Handle failure
            if production_mode:
                logger.error("Parallel data collection failed in production mode")
                return {
                    'collection_success': False,
                    'error': 'All data sources failed - cannot generate production content without real data',
                    'data_source': 'Failed',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Use minimal cached data in test mode
                logger.warning("Parallel collection failed, using minimal cached data (test mode only)")
                cached_data = self._create_minimal_cached_data(symbols[:5])
                market_summary = self._create_market_summary(cached_data)
                
                return {
                    'market_summary': market_summary,
                    'winners': cached_data[:2],
                    'losers': cached_data[-2:] if len(cached_data) >= 2 else cached_data,
                    'all_data': cached_data,
                    'collection_success': True,
                    'data_source': 'Minimal Cached Data',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Parallel collection failed: {str(e)}")
            return {
                'collection_success': False,
                'error': str(e),
                'data_source': 'Failed',
                'timestamp': datetime.now().isoformat()
            }
        finally:
            # Final garbage collection
            gc.collect()
    
    def _create_market_summary(self, data: List[Dict]) -> Dict:
        """Create market summary from collected data"""
        if not data:
            return {}
        
        # Calculate summary statistics efficiently
        advancing = sum(1 for stock in data if stock.get('percent_change', 0) > 0)
        declining = sum(1 for stock in data if stock.get('percent_change', 0) < 0)
        avg_change = sum(stock.get('percent_change', 0) for stock in data) / len(data)
        
        # Get top winners and losers efficiently
        sorted_data = sorted(data, key=lambda x: x.get('percent_change', 0), reverse=True)
        winners = sorted_data[:5]
        losers = sorted_data[-5:] if len(sorted_data) >= 5 else sorted_data
        
        return {
            'total_stocks_analyzed': len(data),
            'advancing_stocks': advancing,
            'declining_stocks': declining,
            'average_change': round(avg_change, 2),
            'market_sentiment': 'Mixed',
            'market_date': datetime.now().isoformat(),
            'collection_timestamp': datetime.now().isoformat(),
            'data_source': 'Yahoo Finance (Parallel)',
            'market_coverage': f"Analyzing {len(data)} representative stocks"
        }
    
    def _create_minimal_cached_data(self, symbols: List[str]) -> List[Dict]:
        """Create minimal cached data for testing"""
        cached_data = []
        for i, symbol in enumerate(symbols):
            base_price = 100 + (i * 10)
            change_percent = (i % 3 - 1) * 2.5
            price_change = base_price * (change_percent / 100)
            market_cap = 10_000_000_000 + (i * 1_000_000_000)
            
            cached_data.append({
                'symbol': symbol,
                'current_price': round(base_price + price_change, 2),
                'previous_price': round(base_price, 2),
                'price_change': round(price_change, 2),
                'percent_change': round(change_percent, 2),
                'current_volume': 1_000_000 + (i * 100_000),
                'average_volume': 1_000_000,
                'volume_ratio': 1.0 + (i * 0.1),
                'market_cap': market_cap,
                'timestamp': datetime.now().isoformat()
            })
        
        return cached_data


# Global instance
parallel_collector = ParallelCollector() 