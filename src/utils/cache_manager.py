"""
Cache Manager for Market Voices
Implements intelligent caching to reduce API calls and costs
"""
import time
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
import pickle
import os

from ..config.settings import get_settings


class CacheManager:
    """Manages intelligent caching for API calls and data"""
    
    def __init__(self):
        self.settings = get_settings()
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache configuration
        self.cache_config = {
            "stock_data": {
                "ttl_minutes": 15,  # Stock data cache for 15 minutes
                "max_size_mb": 50,
                "enabled": True
            },
            "news_data": {
                "ttl_minutes": 60,  # News data cache for 1 hour
                "max_size_mb": 100,
                "enabled": True
            },
            "market_news": {
                "ttl_minutes": 30,  # Market news cache for 30 minutes
                "max_size_mb": 25,
                "enabled": True
            },
            "symbol_lists": {
                "ttl_minutes": 1440,  # Symbol lists cache for 24 hours
                "max_size_mb": 5,
                "enabled": True
            },
            "technical_indicators": {
                "ttl_minutes": 30,  # Technical indicators cache for 30 minutes
                "max_size_mb": 20,
                "enabled": True
            }
        }
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "saves": 0,
            "evictions": 0,
            "total_savings_requests": 0
        }
    
    def _generate_cache_key(self, category: str, identifier: str, **kwargs) -> str:
        """Generate a unique cache key"""
        # Create a hash of the identifier and additional parameters
        key_data = f"{category}:{identifier}"
        if kwargs:
            # Sort kwargs for consistent hashing
            sorted_kwargs = sorted(kwargs.items())
            key_data += ":" + json.dumps(sorted_kwargs, sort_keys=True)
        
        # Create hash and return filename
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{category}_{key_hash}.cache"
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the full path for a cache file"""
        return self.cache_dir / cache_key
    
    def _is_cache_valid(self, cache_path: Path, ttl_minutes: int) -> bool:
        """Check if cache file is still valid"""
        if not cache_path.exists():
            return False
        
        # Check file age
        file_age = time.time() - cache_path.stat().st_mtime
        max_age = ttl_minutes * 60  # Convert to seconds
        
        return file_age < max_age
    
    def _get_cache_size_mb(self, cache_path: Path) -> float:
        """Get cache file size in MB"""
        if not cache_path.exists():
            return 0.0
        return cache_path.stat().st_size / (1024 * 1024)
    
    def _cleanup_expired_cache(self, category: str):
        """Remove expired cache files for a category"""
        config = self.cache_config.get(category, {})
        if not config.get("enabled", False):
            return
        
        ttl_minutes = config.get("ttl_minutes", 60)
        pattern = f"{category}_*.cache"
        
        for cache_file in self.cache_dir.glob(pattern):
            if not self._is_cache_valid(cache_file, ttl_minutes):
                try:
                    cache_file.unlink()
                    logger.debug(f"Removed expired cache: {cache_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to remove expired cache {cache_file.name}: {str(e)}")
    
    def _enforce_size_limit(self, category: str):
        """Enforce size limits by removing oldest files"""
        config = self.cache_config.get(category, {})
        max_size_mb = config.get("max_size_mb", 50)
        
        pattern = f"{category}_*.cache"
        cache_files = list(self.cache_dir.glob(pattern))
        
        if not cache_files:
            return
        
        # Calculate total size
        total_size = sum(self._get_cache_size_mb(f) for f in cache_files)
        
        if total_size <= max_size_mb:
            return
        
        # Sort by modification time (oldest first)
        cache_files.sort(key=lambda f: f.stat().st_mtime)
        
        # Remove oldest files until under limit
        for cache_file in cache_files:
            if total_size <= max_size_mb:
                break
            
            file_size = self._get_cache_size_mb(cache_file)
            try:
                cache_file.unlink()
                total_size -= file_size
                self.stats["evictions"] += 1
                logger.debug(f"Evicted cache file: {cache_file.name}")
            except Exception as e:
                logger.warning(f"Failed to evict cache file {cache_file.name}: {str(e)}")
    
    def get(self, category: str, identifier: str, **kwargs) -> Optional[Any]:
        """Get data from cache"""
        config = self.cache_config.get(category, {})
        if not config.get("enabled", False):
            self.stats["misses"] += 1
            return None
        
        # Cleanup expired cache first
        self._cleanup_expired_cache(category)
        
        # Generate cache key and path
        cache_key = self._generate_cache_key(category, identifier, **kwargs)
        cache_path = self._get_cache_path(cache_key)
        
        # Check if cache is valid
        ttl_minutes = config.get("ttl_minutes", 60)
        if not self._is_cache_valid(cache_path, ttl_minutes):
            self.stats["misses"] += 1
            return None
        
        try:
            # Load cached data
            with open(cache_path, 'rb') as f:
                cached_data = pickle.load(f)
            
            self.stats["hits"] += 1
            logger.debug(f"Cache hit: {category}/{identifier}")
            return cached_data
            
        except Exception as e:
            logger.warning(f"Failed to load cache {cache_path}: {str(e)}")
            self.stats["misses"] += 1
            return None
    
    def set(self, category: str, identifier: str, data: Any, **kwargs) -> bool:
        """Store data in cache"""
        config = self.cache_config.get(category, {})
        if not config.get("enabled", False):
            return False
        
        # Generate cache key and path
        cache_key = self._generate_cache_key(category, identifier, **kwargs)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            # Enforce size limits before saving
            self._enforce_size_limit(category)
            
            # Save data
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            
            self.stats["saves"] += 1
            logger.debug(f"Cache save: {category}/{identifier}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cache {cache_path}: {str(e)}")
            return False
    
    def invalidate(self, category: str, identifier: str = None, **kwargs) -> bool:
        """Invalidate cache entries"""
        if identifier:
            # Invalidate specific entry
            cache_key = self._generate_cache_key(category, identifier, **kwargs)
            cache_path = self._get_cache_path(cache_key)
            
            if cache_path.exists():
                try:
                    cache_path.unlink()
                    logger.debug(f"Invalidated cache: {category}/{identifier}")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to invalidate cache {cache_path}: {str(e)}")
                    return False
        else:
            # Invalidate all entries for category
            pattern = f"{category}_*.cache"
            invalidated = 0
            
            for cache_file in self.cache_dir.glob(pattern):
                try:
                    cache_file.unlink()
                    invalidated += 1
                except Exception as e:
                    logger.warning(f"Failed to invalidate cache {cache_file.name}: {str(e)}")
            
            logger.debug(f"Invalidated {invalidated} cache entries for category: {category}")
            return invalidated > 0
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hit_rate = 0.0
        total_requests = self.stats["hits"] + self.stats["misses"]
        if total_requests > 0:
            hit_rate = (self.stats["hits"] / total_requests) * 100
        
        # Calculate cache size
        total_size_mb = 0.0
        cache_files = list(self.cache_dir.glob("*.cache"))
        for cache_file in cache_files:
            total_size_mb += self._get_cache_size_mb(cache_file)
        
        return {
            **self.stats,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "cache_files": len(cache_files),
            "total_size_mb": round(total_size_mb, 2),
            "estimated_api_savings": self.stats["hits"]  # Each hit saves one API call
        }
    
    def clear_all(self) -> bool:
        """Clear all cache data"""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
            
            # Reset stats
            self.stats = {
                "hits": 0,
                "misses": 0,
                "saves": 0,
                "evictions": 0,
                "total_savings_requests": 0
            }
            
            logger.info("All cache data cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
            return False
    
    def optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache by removing expired files and enforcing limits"""
        optimization_results = {
            "expired_removed": 0,
            "size_evictions": 0,
            "total_size_before_mb": 0,
            "total_size_after_mb": 0
        }
        
        # Calculate size before
        cache_files = list(self.cache_dir.glob("*.cache"))
        optimization_results["total_size_before_mb"] = sum(
            self._get_cache_size_mb(f) for f in cache_files
        )
        
        # Cleanup expired cache for all categories
        for category in self.cache_config.keys():
            self._cleanup_expired_cache(category)
            self._enforce_size_limit(category)
        
        # Calculate size after
        cache_files_after = list(self.cache_dir.glob("*.cache"))
        optimization_results["total_size_after_mb"] = sum(
            self._get_cache_size_mb(f) for f in cache_files_after
        )
        
        logger.info(f"Cache optimization completed. Size: {optimization_results['total_size_before_mb']:.2f}MB → {optimization_results['total_size_after_mb']:.2f}MB")
        
        return optimization_results


# Global cache manager instance
cache_manager = CacheManager()


# Decorator for caching function results
def cached(category: str, ttl_minutes: int = None):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache identifier from function name and arguments
            identifier = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Use provided TTL or default from config
            if ttl_minutes is None:
                config_ttl = cache_manager.cache_config.get(category, {}).get("ttl_minutes", 60)
            else:
                config_ttl = ttl_minutes
            
            # Try to get from cache
            cached_result = cache_manager.get(category, identifier)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(category, identifier, result)
            
            return result
        
        return wrapper
    return decorator


# Specific cache decorators for common use cases
def cache_stock_data(func):
    """Cache stock data for 15 minutes"""
    return cached("stock_data", 15)(func)


def cache_news_data(func):
    """Cache news data for 1 hour"""
    return cached("news_data", 60)(func)


def cache_market_news(func):
    """Cache market news for 30 minutes"""
    return cached("market_news", 30)(func)


def cache_symbol_lists(func):
    """Cache symbol lists for 24 hours"""
    return cached("symbol_lists", 1440)(func)


def cache_technical_indicators(func):
    """Cache technical indicators for 30 minutes"""
    return cached("technical_indicators", 30)(func) 