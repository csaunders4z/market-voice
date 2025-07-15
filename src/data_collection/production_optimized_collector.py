"""
Production-optimized data collector with enhanced rate limiting and error handling
Addresses the 100+ Finnhub 422 errors and API rate limiting issues found in production workflow
"""
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from loguru import logger

from .unified_data_collector import UnifiedDataCollector


class ProductionOptimizedCollector(UnifiedDataCollector):
    """Enhanced data collector optimized for production with aggressive rate limiting"""
    
    def __init__(self):
        super().__init__()
        
        self.api_delays = {
            'finnhub': 1.0,    # 1s between Finnhub calls (increased from 0.5s)
            'fmp': 0.5,        # 500ms between FMP calls
            'news': 2.0,       # 2s between news API calls (increased from 1s)
            'yahoo': 0.2,      # 200ms between Yahoo calls (reliable)
            'default': 0.3     # 300ms default delay
        }
        
        self.batch_sizes = {
            'finnhub': 5,      # Very small batches for Finnhub (reduced from 10)
            'fmp': 10,         # Small batches for FMP
            'yahoo': 30,       # Larger batches for Yahoo (more reliable)
            'news': 3,         # Very small batches for news APIs
            'default': 15      # Reduced default batch size
        }
        
        self.max_consecutive_failures = {
            'finnhub': 3,      # Reduced from 5 for faster circuit breaking
            'fmp': 5,
            'news': 5,
            'default': 5
        }
        
        self.recovery_delays = {
            'finnhub': 300,    # 5 minutes recovery for Finnhub
            'fmp': 180,        # 3 minutes recovery for FMP
            'news': 120,       # 2 minutes recovery for news APIs
            'default': 240     # 4 minutes default recovery
        }
        
        self.api_health = {
            'finnhub': {'failures': 0, 'disabled_until': None},
            'fmp': {'failures': 0, 'disabled_until': None},
            'news': {'failures': 0, 'disabled_until': None}
        }
    
    def _is_api_healthy(self, api_name: str) -> bool:
        """Check if API is healthy and not in recovery period"""
        health = self.api_health.get(api_name, {'failures': 0, 'disabled_until': None})
        
        if health['disabled_until'] and time.time() > health['disabled_until']:
            logger.info(f"{api_name} API recovery period elapsed, re-enabling")
            health['failures'] = 0
            health['disabled_until'] = None
            return True
        
        if health['disabled_until']:
            remaining = int(health['disabled_until'] - time.time())
            logger.warning(f"{api_name} API disabled for {remaining}s")
            return False
        
        return True
    
    def _handle_api_failure(self, api_name: str, error_msg: str):
        """Handle API failure with circuit breaker logic"""
        health = self.api_health.setdefault(api_name, {'failures': 0, 'disabled_until': None})
        health['failures'] += 1
        
        max_failures = self.max_consecutive_failures.get(api_name, 5)
        if health['failures'] >= max_failures:
            recovery_delay = self.recovery_delays.get(api_name, 240)
            health['disabled_until'] = time.time() + recovery_delay
            logger.error(f"{api_name} API disabled for {recovery_delay}s after {max_failures} failures: {error_msg}")
        else:
            logger.warning(f"{api_name} failure {health['failures']}/{max_failures}: {error_msg}")
    
    def _handle_api_success(self, api_name: str):
        """Handle API success - reset failure count"""
        health = self.api_health.setdefault(api_name, {'failures': 0, 'disabled_until': None})
        health['failures'] = 0
    
    def collect_data_with_production_optimization(self, symbols: List[str] = None, max_symbols: int = None) -> Dict:
        """
        Collect data with production-optimized rate limiting and error handling
        Addresses the specific issues found in the 516-symbol production workflow
        """
        start_time = time.time()
        
        if symbols is None:
            from .symbol_loader import symbol_loader
            nasdaq_symbols = symbol_loader.get_nasdaq_100_symbols()
            sp500_symbols = symbol_loader.get_sp_500_symbols()
            symbols = list(set(nasdaq_symbols + sp500_symbols))  # Remove duplicates
        
        if max_symbols:
            symbols = symbols[:max_symbols]
        
        logger.info(f"Starting production-optimized data collection for {len(symbols)} symbols")
        
        batch_size = self.batch_sizes.get('default', 15)
        batches = [symbols[i:i + batch_size] for i in range(0, len(symbols), batch_size)]
        
        logger.info(f"Processing {len(batches)} batches of up to {batch_size} symbols each")
        
        all_data = {}
        successful_collections = 0
        failed_collections = 0
        api_error_counts = {'finnhub': 0, 'fmp': 0, 'news': 0, 'yahoo': 0}
        
        for batch_idx, batch in enumerate(batches, 1):
            logger.info(f"Processing batch {batch_idx}/{len(batches)} ({len(batch)} symbols)")
            
            batch_data, batch_errors = self._collect_batch_with_production_optimization(batch)
            all_data.update(batch_data)
            
            for api, count in batch_errors.items():
                api_error_counts[api] += count
            
            for symbol, data in batch_data.items():
                if data and any(data.values() if isinstance(data, dict) else [data]):
                    successful_collections += 1
                else:
                    failed_collections += 1
            
            if batch_idx < len(batches):
                base_delay = 3.0  # Increased base delay for production
                
                total_errors = sum(api_error_counts.values())
                if total_errors > 10:
                    delay = min(base_delay * (1.5 ** (total_errors // 10)), 15.0)
                    logger.warning(f"Applying exponential backoff: {delay:.1f}s due to {total_errors} total API errors")
                    time.sleep(delay)
                else:
                    time.sleep(base_delay)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Production-optimized data collection completed in {duration:.1f} seconds")
        logger.info(f"Successful: {successful_collections}, Failed: {failed_collections}")
        logger.info(f"API Error Summary: {api_error_counts}")
        
        return {
            'data': all_data,
            'metadata': {
                'total_symbols': len(symbols),
                'successful_collections': successful_collections,
                'failed_collections': failed_collections,
                'duration_seconds': duration,
                'batches_processed': len(batches),
                'api_error_counts': api_error_counts,
                'api_health_status': self.api_health
            }
        }
    
    def _collect_batch_with_production_optimization(self, symbols: List[str]) -> Tuple[Dict[str, Dict], Dict[str, int]]:
        """Collect data for a batch with production-optimized error handling"""
        batch_data = {}
        error_counts = {'finnhub': 0, 'fmp': 0, 'news': 0, 'yahoo': 0}
        
        for symbol in symbols:
            symbol_data = {}
            
            try:
                yahoo_data = self._collect_yahoo_data_safe(symbol)
                if yahoo_data:
                    symbol_data.update(yahoo_data)
                    self._handle_api_success('yahoo')
                    time.sleep(self.api_delays.get('yahoo', 0.2))
                else:
                    error_counts['yahoo'] += 1
            except Exception as e:
                error_counts['yahoo'] += 1
                self._handle_api_failure('yahoo', str(e))
                logger.warning(f"Yahoo Finance collection failed for {symbol}: {e}")
            
            if symbol_data.get('current_price') and self._is_api_healthy('finnhub'):
                try:
                    finnhub_data = self._collect_finnhub_data_safe(symbol)
                    if finnhub_data:
                        for key, value in finnhub_data.items():
                            if key not in symbol_data or not symbol_data[key]:
                                symbol_data[key] = value
                        self._handle_api_success('finnhub')
                    else:
                        error_counts['finnhub'] += 1
                        self._handle_api_failure('finnhub', f"No data returned for {symbol}")
                    
                    time.sleep(self.api_delays.get('finnhub', 1.0))
                except Exception as e:
                    error_counts['finnhub'] += 1
                    self._handle_api_failure('finnhub', str(e))
                    logger.warning(f"Finnhub collection failed for {symbol}: {e}")
            
            if not symbol_data.get('company_name') and self._is_api_healthy('fmp'):
                try:
                    fmp_data = self._collect_fmp_data_safe(symbol)
                    if fmp_data:
                        for key, value in fmp_data.items():
                            if key not in symbol_data or not symbol_data[key]:
                                symbol_data[key] = value
                        self._handle_api_success('fmp')
                    else:
                        error_counts['fmp'] += 1
                        self._handle_api_failure('fmp', f"No data returned for {symbol}")
                    
                    time.sleep(self.api_delays.get('fmp', 0.5))
                except Exception as e:
                    error_counts['fmp'] += 1
                    self._handle_api_failure('fmp', str(e))
                    logger.warning(f"FMP collection failed for {symbol}: {e}")
            
            if len(symbols) <= 50 or symbols.index(symbol) % 5 == 0:  # Every 5th symbol for large batches
                if self._is_api_healthy('news'):
                    try:
                        news_data = self._collect_news_data_safe(symbol)
                        if news_data:
                            symbol_data['news'] = news_data
                            self._handle_api_success('news')
                        else:
                            error_counts['news'] += 1
                            self._handle_api_failure('news', f"No news data for {symbol}")
                        
                        time.sleep(self.api_delays.get('news', 2.0))
                    except Exception as e:
                        error_counts['news'] += 1
                        self._handle_api_failure('news', str(e))
                        logger.warning(f"News collection failed for {symbol}: {e}")
            
            batch_data[symbol] = symbol_data
            
            time.sleep(0.5)  # Increased from 0.3 to 0.5
        
        return batch_data, error_counts
    
    def _collect_yahoo_data_safe(self, symbol: str) -> Optional[Dict]:
        """Safe Yahoo Finance data collection with error handling"""
        try:
            success, data, source = self._collect_yf_data([symbol])
            return data[0] if success and data else None
        except Exception as e:
            logger.warning(f"Yahoo Finance safe collection failed for {symbol}: {e}")
            return None
    
    def _collect_finnhub_data_safe(self, symbol: str) -> Optional[Dict]:
        """Safe Finnhub data collection with error handling"""
        try:
            success, data, source = self._collect_finnhub_data([symbol])
            return data[0] if success and data else None
        except Exception as e:
            logger.warning(f"Finnhub safe collection failed for {symbol}: {e}")
            return None
    
    def _collect_fmp_data_safe(self, symbol: str) -> Optional[Dict]:
        """Safe FMP data collection with error handling"""
        try:
            success, data, source = self._collect_fmp_data([symbol])
            return data[0] if success and data else None
        except Exception as e:
            logger.warning(f"FMP safe collection failed for {symbol}: {e}")
            return None
    
    def _collect_news_data_safe(self, symbol: str) -> Optional[Dict]:
        """Safe news data collection with error handling"""
        try:
            from .news_collector import news_collector
            news_data = news_collector.get_company_news(symbol, limit=3)
            return news_data if news_data else None
        except Exception as e:
            logger.warning(f"News safe collection failed for {symbol}: {e}")
            return None


production_optimized_collector = ProductionOptimizedCollector()
