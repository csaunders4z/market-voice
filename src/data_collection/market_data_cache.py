"""
Market data caching utility for storing and retrieving stock market data with TTL.
This helps reduce API calls and speed up development.
"""
import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import hashlib
import logging

from src.utils.cache import APICache

logger = logging.getLogger(__name__)

class MarketDataCache:
    """Cache for market data with TTL support."""
    
    def __init__(self, cache_dir: str = "cache/market_data", ttl_hours: int = 12):
        """
        Initialize the market data cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Default time-to-live for cache entries in hours
        """
        self.cache = APICache(cache_dir=cache_dir, ttl_hours=ttl_hours)
        
    def get_gainers_losers(self, exchange: str = "NASDAQ") -> Optional[Dict[str, List[Dict]]]:
        """
        Get cached gainers and losers for an exchange.
        
        Args:
            exchange: Exchange symbol (e.g., 'NASDAQ', 'NYSE')
            
        Returns:
            Dict with 'gainers' and 'losers' lists if found, else None
        """
        cache_key = f"market_data:gainers_losers:{exchange.lower()}"
        return self.cache.get(cache_key)
    
    def set_gainers_losers(self, exchange: str, gainers: List[Dict], losers: List[Dict]) -> None:
        """
        Cache gainers and losers for an exchange.
        
        Args:
            exchange: Exchange symbol (e.g., 'NASDAQ', 'NYSE')
            gainers: List of gainer stocks
            losers: List of loser stocks
        """
        cache_key = f"market_data:gainers_losers:{exchange.lower()}"
        data = {
            'exchange': exchange,
            'timestamp': datetime.now().isoformat(),
            'gainers': gainers,
            'losers': losers
        }
        self.cache.set(cache_key, data)
    
    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """
        Get cached stock data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Cached stock data if found and not expired, else None
        """
        cache_key = f"stock_data:{symbol.upper()}"
        return self.cache.get(cache_key)
    
    def set_stock_data(self, symbol: str, data: Dict) -> None:
        """
        Cache stock data for a symbol.
        
        Args:
            symbol: Stock symbol
            data: Stock data to cache
        """
        cache_key = f"stock_data:{symbol.upper()}"
        self.cache.set(cache_key, data)
    
    def get_market_news(self, query: str = "market") -> Optional[List[Dict]]:
        """
        Get cached market news.
        
        Args:
            query: News query string
            
        Returns:
            Cached market news if found and not expired, else None
        """
        cache_key = f"market_news:{query.lower()}"
        return self.cache.get(cache_key)
    
    def set_market_news(self, query: str, news: List[Dict]) -> None:
        """
        Cache market news.
        
        Args:
            query: News query string
            news: List of news articles
        """
        cache_key = f"market_news:{query.lower()}"
        self.cache.set(cache_key, news)
    
    def clear_expired(self) -> None:
        """Clear all expired cache entries."""
        self.cache.clear_expired()

# Global instance
market_data_cache = MarketDataCache()

def cache_market_data(ttl_hours: int = 12):
    """
    Decorator to cache market data API calls.
    
    Args:
        ttl_hours: Time-to-live for cache entries in hours
        
    Returns:
        Decorated function with caching
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create a cache key based on function name and arguments
            cache_key_parts = [f"market_data:{func.__name__}"]
            
            # Add positional args to key
            for arg in args:
                if isinstance(arg, (str, int, float, bool, type(None))):
                    cache_key_parts.append(str(arg))
            
            # Add keyword args to key
            for k, v in sorted(kwargs.items()):
                if v is not None and k != 'self':  # Skip self reference for methods
                    cache_key_parts.append(f"{k}={v}")
            
            cache_key = ":".join(cache_key_parts)
            
            # Try to get from cache
            cached_result = market_data_cache.cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Using cached market data for {func.__name__}")
                return cached_result
            
            # Call the function if not in cache
            result = func(*args, **kwargs)
            
            # Cache the result
            if result is not None:
                market_data_cache.cache.set(cache_key, result)
                
            return result
        return wrapper
    return decorator
