"""
Caching utility for API responses with TTL (Time To Live) support.
This helps reduce API calls, avoid rate limiting, and speed up development.
"""
import os
import json
import time
import hashlib
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, cast
from functools import wraps
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Type variable for generic function typing
T = TypeVar('T')

class APICache:
    """A simple file-based cache for API responses with TTL support."""
    
    def __init__(self, cache_dir: str = "cache", ttl_hours: int = 12):
        """
        Initialize the cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Default time-to-live for cache entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_hours * 3600
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """Get the filesystem path for a cache key."""
        # Create a safe filename from the key
        key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
        return self.cache_dir / f"{key_hash}.json"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found and not expired, else None
        """
        cache_file = self._get_cache_path(key)
        
        if not cache_file.exists():
            return None
            
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Check if cache entry is expired
            cache_time = datetime.fromisoformat(data['timestamp'])
            if (datetime.now() - cache_time).total_seconds() > self.ttl_seconds:
                logger.debug(f"Cache expired for key: {key}")
                return None
                
            logger.debug(f"Cache hit for key: {key}")
            return data['value']
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Error reading cache for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Store a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
        """
        cache_file = self._get_cache_path(key)
        
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'value': value
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"Cached data for key: {key}")
            
        except (TypeError, OverflowError) as e:
            logger.error(f"Failed to cache value for key {key}: {e}")
    
    def clear_expired(self) -> None:
        """Remove all expired cache entries."""
        logger.info("Clearing expired cache entries...")
        now = time.time()
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                file_time = cache_file.stat().st_mtime
                if now - file_time > self.ttl_seconds:
                    cache_file.unlink()
                    logger.debug(f"Removed expired cache file: {cache_file}")
            except OSError as e:
                logger.warning(f"Error processing cache file {cache_file}: {e}")

# Global cache instance with default 12-hour TTL
api_cache = APICache()

def cached(ttl_hours: int = 12, key_prefix: str = ""):
    """
    Decorator to cache function results with TTL.
    
    Args:
        ttl_hours: Time-to-live for cache entries in hours
        key_prefix: Optional prefix for cache keys
        
    Returns:
        Decorated function with caching
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Create a cache key from function name and arguments
            cache_key_parts = [key_prefix, func.__name__]
            
            # Add positional args to key
            for arg in args:
                if isinstance(arg, (str, int, float, bool, type(None))):
                    cache_key_parts.append(str(arg))
            
            # Add keyword args to key
            for k, v in sorted(kwargs.items()):
                if v is not None and k != 'self':  # Skip self reference for methods
                    cache_key_parts.append(f"{k}={v}")
            
            cache_key = ":".join(cache_key_parts)
            cache = APICache(ttl_hours=ttl_hours)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Using cached result for {func.__name__}")
                return cached_result
            
            # Call the function if not in cache
            result = func(*args, **kwargs)
            
            # Cache the result
            if result is not None:
                cache.set(cache_key, result)
                
            return result
            
        return cast(Callable[..., T], wrapper)
    return decorator
