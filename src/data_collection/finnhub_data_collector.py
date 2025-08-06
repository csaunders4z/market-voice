"""
Finnhub Data Collector for Market Voice
Provides market data, fundamentals, and news endpoints with global circuit breaker/session disable logic.
"""
import os
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
import requests

from src.config.settings import get_settings
from src.utils.rate_limiter import rate_limiter

class FinnhubDataCollector:
    """Collects data from Finnhub with robust error handling and circuit breaker/session disable logic."""
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.finnhub_api_key or os.getenv("FINNHUB_API_KEY", "")
        self._finnhub_consecutive_failures = 0
        self._finnhub_failure_threshold = self.settings.finnhub_failure_threshold
        self._finnhub_disabled_for_session = False
        self.base_url = "https://finnhub.io/api/v1"
        self.news_days_back = 4  # configurable days back for news collection
        self.rate_limiter = rate_limiter

    def _check_disabled(self) -> bool:
        if self._finnhub_disabled_for_session:
            logger.error(f"Finnhub API disabled for this session after {self._finnhub_failure_threshold} consecutive failures. Skipping all Finnhub requests.")
            return True
        if not self.api_key or self.api_key == "DUMMY":
            logger.warning("No Finnhub API key available. Skipping Finnhub requests.")
            return True
        return False

    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get real-time quote data for a symbol with rate limiting and retry logic."""
        if self._check_disabled():
            return None
        
        @self.rate_limiter.retry_on_failure(
            max_retries=self.settings.finnhub_max_retries,
            base_delay=self.settings.finnhub_rate_limit_delay
        )
        def _make_request():
            self.rate_limiter._wait_for_rate_limit("finnhub", self.settings.finnhub_rate_limit_delay)
            url = f"{self.base_url}/quote"
            params = {"symbol": symbol, "token": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        try:
            data = _make_request()
            if not data or "c" not in data:
                logger.warning(f"No quote data for {symbol} from Finnhub.")
                self._finnhub_consecutive_failures += 1
                if self._finnhub_consecutive_failures >= self._finnhub_failure_threshold:
                    self._finnhub_disabled_for_session = True
                    logger.error(f"Finnhub API disabled for the remainder of this session after {self._finnhub_failure_threshold} consecutive failures.")
                return None
            self._finnhub_consecutive_failures = 0
            return {
                "symbol": symbol,
                "current_price": data.get("c"),
                "high": data.get("h"),
                "low": data.get("l"),
                "open": data.get("o"),
                "previous_close": data.get("pc"),
                "timestamp": datetime.fromtimestamp(data.get("t", 0)).isoformat() if data.get("t") else None
            }
        except Exception as e:
            self._finnhub_consecutive_failures += 1
            if self._finnhub_consecutive_failures >= self._finnhub_failure_threshold:
                self._finnhub_disabled_for_session = True
                logger.error(f"Finnhub API disabled for the remainder of this session after {self._finnhub_failure_threshold} consecutive failures (exception path).")
            
            self.rate_limiter._handle_rate_limit_error("finnhub", e)
            logger.error(f"Finnhub quote fetch failed for {symbol}: {str(e)}")
            return None

    def get_company_profile(self, symbol: str) -> Optional[Dict]:
        """Get company profile for a symbol with rate limiting and retry logic."""
        if self._check_disabled():
            return None
        
        @self.rate_limiter.retry_on_failure(
            max_retries=self.settings.finnhub_max_retries,
            base_delay=self.settings.finnhub_rate_limit_delay
        )
        def _make_request():
            self.rate_limiter._wait_for_rate_limit("finnhub", self.settings.finnhub_rate_limit_delay)
            url = f"{self.base_url}/stock/profile2"
            params = {"symbol": symbol, "token": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        try:
            data = _make_request()
            if not data or "name" not in data:
                logger.warning(f"No profile data for {symbol} from Finnhub.")
                self._finnhub_consecutive_failures += 1
                if self._finnhub_consecutive_failures >= self._finnhub_failure_threshold:
                    self._finnhub_disabled_for_session = True
                    logger.error(f"Finnhub API disabled for the remainder of this session after {self._finnhub_failure_threshold} consecutive failures.")
                return None
            self._finnhub_consecutive_failures = 0
            return data
        except Exception as e:
            self._finnhub_consecutive_failures += 1
            if self._finnhub_consecutive_failures >= self._finnhub_failure_threshold:
                self._finnhub_disabled_for_session = True
                logger.error(f"Finnhub API disabled for the remainder of this session after {self._finnhub_failure_threshold} consecutive failures (exception path).")
            
            self.rate_limiter._handle_rate_limit_error("finnhub", e)
            logger.error(f"Finnhub profile fetch failed for {symbol}: {str(e)}")
            return None

    def get_news(self, symbol: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict]:
        """Get company-specific news from Finnhub with rate limiting and retry logic."""
        if self._check_disabled():
            return []
        
        @self.rate_limiter.retry_on_failure(
            max_retries=self.settings.finnhub_max_retries,
            base_delay=self.settings.finnhub_rate_limit_delay
        )
        def _make_request():
            self.rate_limiter._wait_for_rate_limit("finnhub", self.settings.finnhub_rate_limit_delay)
            if not from_date:
                from_date_calc = (datetime.now() - timedelta(days=self.news_days_back)).strftime('%Y-%m-%d')
            else:
                from_date_calc = from_date
            if not to_date:
                to_date_calc = datetime.now().strftime('%Y-%m-%d')
            else:
                to_date_calc = to_date
                
            url = f"{self.base_url}/company-news"
            params = {"symbol": symbol, "from": from_date_calc, "to": to_date_calc, "token": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        try:
            data = _make_request()
            if not data or not isinstance(data, list):
                logger.warning(f"No news data for {symbol} from Finnhub.")
                self._finnhub_consecutive_failures += 1
                if self._finnhub_consecutive_failures >= self._finnhub_failure_threshold:
                    self._finnhub_disabled_for_session = True
                    logger.error(f"Finnhub API disabled for the remainder of this session after {self._finnhub_failure_threshold} consecutive failures.")
                return []
            self._finnhub_consecutive_failures = 0
            return data
        except Exception as e:
            self._finnhub_consecutive_failures += 1
            if self._finnhub_consecutive_failures >= self._finnhub_failure_threshold:
                self._finnhub_disabled_for_session = True
                logger.error(f"Finnhub API disabled for the remainder of this session after {self._finnhub_failure_threshold} consecutive failures (exception path).")
            
            self.rate_limiter._handle_rate_limit_error("finnhub", e)
            logger.error(f"Finnhub news fetch failed for {symbol}: {str(e)}")
            return []

    def get_market_news(self, category: str = "general") -> List[Dict]:
        """
        Get market-wide news from Finnhub.
        
        Args:
            category: News category (e.g., 'general', 'forex', 'crypto', 'merger')
            
        Returns:
            List of market news articles
        """
        if self._check_disabled():
            return []
        
        @self.rate_limiter.retry_on_failure(
            max_retries=self.settings.finnhub_max_retries,
            base_delay=self.settings.finnhub_rate_limit_delay
        )
        def _make_request():
            self.rate_limiter._wait_for_rate_limit("finnhub", self.settings.finnhub_rate_limit_delay)
            url = f"{self.base_url}/news"
            params = {
                "category": category,
                "token": self.api_key,
                "minId": ""  # Pagination support if needed
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        try:
            data = _make_request()
            if not data or not isinstance(data, list):
                logger.warning(f"No market news data from Finnhub for category: {category}")
                self._finnhub_consecutive_failures += 1
                if self._finnhub_consecutive_failures >= self._finnhub_failure_threshold:
                    self._finnhub_disabled_for_session = True
                    logger.error(f"Finnhub API disabled for the remainder of this session after {self._finnhub_failure_threshold} consecutive failures.")
                return []
            
            self._finnhub_consecutive_failures = 0
            return data
            
        except Exception as e:
            self._finnhub_consecutive_failures += 1
            if self._finnhub_consecutive_failures >= self._finnhub_failure_threshold:
                self._finnhub_disabled_for_session = True
                logger.error(f"Finnhub API disabled for the remainder of this session after {self._finnhub_failure_threshold} consecutive failures (exception path).")
            
            self.rate_limiter._handle_rate_limit_error("finnhub", e)
            logger.error(f"Finnhub market news fetch failed: {str(e)}")
            return []

# Global instance
finnhub_data_collector = FinnhubDataCollector()
