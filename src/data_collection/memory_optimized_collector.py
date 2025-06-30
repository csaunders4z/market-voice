"""
Memory-Optimized Data Collector for Market Voices
Implements memory optimization techniques for large-scale data collection
"""
import gc
import time
import weakref
from typing import List, Dict, Optional, Tuple, Generator, Iterator
from datetime import datetime
from loguru import logger
import os
import yfinance as yf
import psutil

from ..config.settings import get_settings
from ..utils.rate_limiter import rate_limiter
from .fmp_stock_data import fmp_stock_collector
from .news_collector import news_collector
from .economic_calendar import economic_calendar
from .free_news_sources import free_news_collector


class MemoryOptimizedCollector:
    """Memory-optimized data collector with streaming and garbage collection"""
    
    def __init__(self):
        self.settings = get_settings()
        self.memory_threshold_mb = 2048  # 2GB threshold
        self.batch_size = 10  # Smaller batches for memory management
        self._monitor_memory = True
        
    def _check_memory_usage(self) -> float:
        """Check current memory usage and force garbage collection if needed"""
        if not self._monitor_memory:
            return 0.0
            
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if memory_mb > self.memory_threshold_mb:
            logger.warning(f"High memory usage detected: {memory_mb:.1f} MB, forcing garbage collection")
            gc.collect()
            memory_mb = process.memory_info().rss / 1024 / 1024
            logger.info(f"Memory after GC: {memory_mb:.1f} MB")
        
        return memory_mb
    
    def _stream_symbols(self, symbols: List[str]) -> Generator[List[str], None, None]:
        """Stream symbols in small batches to reduce memory footprint"""
        for i in range(0, len(symbols), self.batch_size):
            batch = symbols[i:i + self.batch_size]
            yield batch
            # Check memory after each batch
            self._check_memory_usage()
    
    def _minimal_stock_data(self, symbol: str, ticker: yf.Ticker) -> Optional[Dict]:
        """Create minimal stock data structure to reduce memory usage"""
        try:
            # Get only essential data
            info = ticker.info
            hist = ticker.history(period="2d")
            
            if len(hist) < 2:
                return None
            
            current_price = hist['Close'].iloc[-1]
            previous_price = hist['Close'].iloc[-2]
            price_change = current_price - previous_price
            percent_change = (price_change / previous_price) * 100
            
            # Create minimal data structure
            stock_data = {
                'symbol': symbol,
                'company_name': info.get('longName', symbol)[:50],  # Limit string length
                'current_price': round(current_price, 2),
                'previous_price': round(previous_price, 2),
                'price_change': round(price_change, 2),
                'percent_change': round(percent_change, 2),
                'current_volume': int(hist['Volume'].iloc[-1]),
                'average_volume': int(info.get('averageVolume', hist['Volume'].iloc[-1])),
                'market_cap': int(info.get('marketCap', 0)),
                'timestamp': datetime.now().isoformat()
            }
            
            # Clear references to free memory
            del info, hist, ticker
            
            return stock_data
            
        except Exception as e:
            logger.warning(f"Failed to fetch minimal data for {symbol}: {str(e)}")
            return None
    
    def _collect_yf_data_streaming(self, symbols: List[str]) -> Iterator[Dict]:
        """Collect Yahoo Finance data using streaming approach"""
        logger.info(f"Starting streaming data collection for {len(symbols)} symbols")
        
        total_processed = 0
        total_successful = 0
        
        for batch in self._stream_symbols(symbols):
            logger.info(f"Processing batch of {len(batch)} symbols (total: {total_processed}/{len(symbols)})")
            
            batch_results = []
            
            for symbol in batch:
                try:
                    ticker = yf.Ticker(symbol)
                    stock_data = self._minimal_stock_data(symbol, ticker)
                    
                    if stock_data:
                        batch_results.append(stock_data)
                        total_successful += 1
                    
                    total_processed += 1
                    
                    # Yield results immediately to free memory
                    if stock_data:
                        yield stock_data
                    
                    # Clear ticker reference
                    del ticker
                    
                except Exception as e:
                    logger.warning(f"Error processing {symbol}: {str(e)}")
                    total_processed += 1
                    continue
            
            # Clear batch results
            del batch_results
            
            # Force garbage collection after each batch
            gc.collect()
            
            # Rate limiting between batches
            time.sleep(0.1)
        
        logger.info(f"Streaming collection completed: {total_successful}/{total_processed} symbols successful")
    
    def _collect_data_with_memory_management(self, symbols: List[str]) -> Tuple[bool, List[Dict], str]:
        """Collect data with comprehensive memory management"""
        try:
            logger.info("Starting memory-optimized data collection")
            
            # Initial memory check
            initial_memory = self._check_memory_usage()
            logger.info(f"Initial memory usage: {initial_memory:.1f} MB")
            
            # Use streaming collection
            collected_data = []
            
            for stock_data in self._collect_yf_data_streaming(symbols):
                collected_data.append(stock_data)
                
                # Check memory every 20 items
                if len(collected_data) % 20 == 0:
                    current_memory = self._check_memory_usage()
                    logger.info(f"Collected {len(collected_data)} items, memory: {current_memory:.1f} MB")
            
            # Final memory check
            final_memory = self._check_memory_usage()
            logger.info(f"Final memory usage: {final_memory:.1f} MB (delta: {final_memory - initial_memory:.1f} MB)")
            
            if collected_data:
                logger.info(f"Memory-optimized collection successful: {len(collected_data)} stocks")
                return True, collected_data, "Yahoo Finance (Memory Optimized)"
            else:
                logger.warning("Memory-optimized collection returned no data")
                return False, [], "Yahoo Finance - No data"
                
        except Exception as e:
            logger.error(f"Memory-optimized collection failed: {str(e)}")
            return False, [], f"Yahoo Finance - {str(e)}"
    
    def _create_lightweight_market_summary(self, data: List[Dict]) -> Dict:
        """Create lightweight market summary to reduce memory usage"""
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
            'data_source': 'Yahoo Finance (Memory Optimized)',
            'market_coverage': f"Analyzing {len(data)} representative stocks"
        }
    
    def collect_data_optimized(self, symbols: List[str] = None, production_mode: bool = True) -> Dict:
        """Collect data with memory optimization"""
        logger.info("Starting memory-optimized data collection")
        
        # Use provided symbols or get from FMP
        if symbols is None:
            symbols = fmp_stock_collector.symbols[:self.settings.max_symbols_per_collection]
        
        # Ensure symbols is a list
        if not isinstance(symbols, list):
            symbols = []
        
        logger.info(f"Collecting data for {len(symbols)} symbols with memory optimization")
        
        # Force initial garbage collection
        gc.collect()
        
        try:
            # Collect data with memory management
            success, data, message = self._collect_data_with_memory_management(symbols)
            
            if success and data:
                # Create lightweight market summary
                market_summary = self._create_lightweight_market_summary(data)
                
                # Get top winners and losers
                sorted_data = sorted(data, key=lambda x: x.get('percent_change', 0), reverse=True)
                winners = [stock for stock in sorted_data if stock.get('percent_change', 0) > 0][:5]
                losers = [stock for stock in sorted_data if stock.get('percent_change', 0) < 0][:5]
                
                result = {
                    'market_summary': market_summary,
                    'winners': winners,
                    'losers': losers,
                    'all_data': data,
                    'collection_success': True,
                    'data_source': message,
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"Memory-optimized data collection successful using {message}")
                return result
            
            # If all sources fail, handle based on production mode
            if production_mode:
                logger.error("Memory-optimized data collection failed in production mode")
                return {
                    'collection_success': False,
                    'error': 'All data sources failed - cannot generate production content without real data',
                    'data_source': 'Failed',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Use minimal cached data in test mode
                logger.warning("Memory-optimized collection failed, using minimal cached data (test mode only)")
                cached_data = self._create_minimal_cached_data(symbols[:5])  # Use very few symbols
                
                market_summary = self._create_lightweight_market_summary(cached_data)
                
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
            logger.error(f"Memory-optimized collection failed: {str(e)}")
            return {
                'collection_success': False,
                'error': str(e),
                'data_source': 'Failed',
                'timestamp': datetime.now().isoformat()
            }
        finally:
            # Final garbage collection
            gc.collect()
    
    def _create_minimal_cached_data(self, symbols: List[str]) -> List[Dict]:
        """Create minimal cached data for testing"""
        cached_data = []
        for i, symbol in enumerate(symbols):
            base_price = 100 + (i * 10)
            change_percent = (i % 3 - 1) * 2.5
            price_change = base_price * (change_percent / 100)
            
            cached_data.append({
                'symbol': symbol,
                'company_name': f'Mock {symbol}',
                'current_price': round(base_price + price_change, 2),
                'previous_price': round(base_price, 2),
                'price_change': round(price_change, 2),
                'percent_change': round(change_percent, 2),
                'current_volume': 1000000,
                'average_volume': 1000000,
                'market_cap': 1000000000,
                'timestamp': datetime.now().isoformat()
            })
        
        return cached_data


# Global instance
memory_optimized_collector = MemoryOptimizedCollector() 