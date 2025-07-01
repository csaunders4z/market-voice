"""
Rate limiting utilities for Market Voices
Provides adaptive rate limiting, retry logic, and batch processing
"""
import time
import random
from typing import List, Dict, Callable, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import asyncio
from functools import wraps

from ..config.settings import get_settings


class RateLimiter:
    """Adaptive rate limiter with retry logic and batch processing"""
    
    def __init__(self):
        self.settings = get_settings()
        self.last_request_time = {}  # Track last request time per API
        self.rate_limit_delays = {}  # Track current delays per API
        self.retry_counts = {}  # Track retry counts per symbol
        self.rate_limit_errors = {}  # Track rate limit errors per API
        
    def _get_delay(self, api_name: str, base_delay: float) -> float:
        """Get adaptive delay for API calls"""
        if not self.settings.enable_adaptive_rate_limiting:
            return base_delay
            
        # Check if we've hit rate limits recently
        if api_name in self.rate_limit_errors:
            last_error_time = self.rate_limit_errors[api_name]
            if datetime.now() - last_error_time < timedelta(minutes=5):
                # Increase delay if we hit rate limits recently
                current_delay = self.rate_limit_delays.get(api_name, base_delay)
                new_delay = min(current_delay * self.settings.rate_limit_backoff_multiplier, 
                              self.settings.max_rate_limit_delay)
                self.rate_limit_delays[api_name] = new_delay
                logger.debug(f"Adaptive delay for {api_name}: {new_delay:.2f}s (rate limited recently)")
                return new_delay
        
        # Gradually decrease delay if no recent errors
        current_delay = self.rate_limit_delays.get(api_name, base_delay)
        if current_delay > base_delay:
            new_delay = max(current_delay * 0.9, base_delay)  # Gradually reduce
            self.rate_limit_delays[api_name] = new_delay
            logger.debug(f"Reducing delay for {api_name}: {new_delay:.2f}s")
            return new_delay
            
        return base_delay
    
    def _wait_for_rate_limit(self, api_name: str, base_delay: float):
        """Wait appropriate time between API calls"""
        delay = self._get_delay(api_name, base_delay)
        
        # Add small random jitter to avoid thundering herd
        jitter = random.uniform(0.1, 0.3)
        total_delay = delay + jitter
        
        # Check if we need to wait
        if api_name in self.last_request_time:
            time_since_last = time.time() - self.last_request_time[api_name]
            if time_since_last < total_delay:
                sleep_time = total_delay - time_since_last
                logger.debug(f"Rate limiting {api_name}: waiting {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self.last_request_time[api_name] = time.time()
    
    def _handle_rate_limit_error(self, api_name: str, error: Exception):
        """Handle rate limit errors and update adaptive delays"""
        if "429" in str(error) or "rate limit" in str(error).lower() or "too many requests" in str(error).lower():
            self.rate_limit_errors[api_name] = datetime.now()
            current_delay = self.rate_limit_delays.get(api_name, 1.0)
            new_delay = min(current_delay * self.settings.rate_limit_backoff_multiplier, 
                          self.settings.max_rate_limit_delay)
            self.rate_limit_delays[api_name] = new_delay
            logger.warning(f"Rate limit hit for {api_name}, increasing delay to {new_delay:.2f}s")
    
    def retry_on_failure(self, max_retries: int = 3, base_delay: float = 1.0):
        """Decorator for retrying failed API calls with exponential backoff"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        
                        # Check if it's a rate limit error
                        if "429" in str(e) or "rate limit" in str(e).lower():
                            self._handle_rate_limit_error(func.__name__, e)
                        
                        if attempt < max_retries:
                            # Exponential backoff
                            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {delay:.2f}s: {str(e)}")
                            time.sleep(delay)
                        else:
                            logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {str(e)}")
                
                raise last_exception
            return wrapper
        return decorator
    
    def batch_process(self, items: List[Any], batch_size: int, batch_delay: float, 
                     process_func: Callable, api_name: str = "unknown", 
                     max_consecutive_errors: int = 5) -> List[Any]:
        """Process items in batches with rate limiting and early termination on persistent errors"""
        results = []
        total_batches = (len(items) + batch_size - 1) // batch_size
        consecutive_errors = 0
        rate_limit_errors = 0
        
        logger.info(f"Processing {len(items)} items in {total_batches} batches for {api_name}")
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.debug(f"Processing batch {batch_num}/{total_batches} for {api_name} ({len(batch)} items)")
            
            # Process batch
            batch_success_count = 0
            for item in batch:
                try:
                    result = process_func(item)
                    if result is not None:
                        results.append(result)
                        batch_success_count += 1
                        consecutive_errors = 0  # Reset on success
                    else:
                        consecutive_errors += 1
                        rate_limit_errors += 1
                except Exception as e:
                    consecutive_errors += 1
                    error_str = str(e)
                    
                    # Check for rate limiting errors
                    if "429" in error_str or "rate limit" in error_str.lower() or "too many requests" in error_str.lower():
                        rate_limit_errors += 1
                        logger.warning(f"Rate limit error for {item} in {api_name}: {error_str}")
                    else:
                        logger.error(f"Error processing {item} in {api_name}: {error_str}")
                    
                    self._handle_rate_limit_error(api_name, e)
                
                # Check if we should stop due to persistent errors
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"Stopping {api_name} collection after {consecutive_errors} consecutive errors")
                    break
                
                # Check if we should stop due to rate limiting
                if rate_limit_errors >= max_consecutive_errors:
                    logger.error(f"Stopping {api_name} collection after {rate_limit_errors} rate limit errors")
                    break
            
            # If entire batch failed, stop processing
            if batch_success_count == 0 and len(batch) > 0:
                logger.error(f"Entire batch {batch_num} failed for {api_name}. Stopping collection.")
                break
            
            # Delay between batches (except for last batch)
            if i + batch_size < len(items) and consecutive_errors < max_consecutive_errors:
                logger.debug(f"Waiting {batch_delay}s between batches for {api_name}")
                time.sleep(batch_delay)
        
        logger.info(f"Completed processing {len(results)}/{len(items)} items for {api_name}")
        return results


class APIRateLimiter:
    """Specific rate limiter for different API types"""
    
    def __init__(self):
        self.settings = get_settings()
        self.rate_limiter = RateLimiter()
    
    def fmp_request(self, func: Callable) -> Callable:
        """Rate limiter for FMP API calls"""
        @self.rate_limiter.retry_on_failure(
            max_retries=self.settings.fmp_max_retries,
            base_delay=self.settings.fmp_rate_limit_delay
        )
        def wrapper(*args, **kwargs):
            self.rate_limiter._wait_for_rate_limit("fmp", self.settings.fmp_rate_limit_delay)
            return func(*args, **kwargs)
        return wrapper
    
    def yahoo_request(self, func: Callable) -> Callable:
        """Rate limiter for Yahoo Finance API calls"""
        @self.rate_limiter.retry_on_failure(
            max_retries=2,
            base_delay=self.settings.yahoo_rate_limit_delay
        )
        def wrapper(*args, **kwargs):
            self.rate_limiter._wait_for_rate_limit("yahoo", self.settings.yahoo_rate_limit_delay)
            return func(*args, **kwargs)
        return wrapper
    
    def alpha_vantage_request(self, func: Callable) -> Callable:
        """Rate limiter for Alpha Vantage API calls"""
        @self.rate_limiter.retry_on_failure(
            max_retries=2,
            base_delay=self.settings.alpha_vantage_rate_limit_delay
        )
        def wrapper(*args, **kwargs):
            self.rate_limiter._wait_for_rate_limit("alpha_vantage", self.settings.alpha_vantage_rate_limit_delay)
            return func(*args, **kwargs)
        return wrapper


# Global instances
rate_limiter = RateLimiter()
api_rate_limiter = APIRateLimiter() 