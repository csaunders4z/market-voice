"""
Finnhub Data Collector for Market Voice
Provides market data, fundamentals, and news endpoints with global circuit breaker/session disable logic.
"""
import os
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from loguru import logger
import requests

from src.config.settings import get_settings

class FinnhubDataCollector:
    """Collects data from Finnhub with robust error handling and circuit breaker/session disable logic."""
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.finnhub_api_key or os.getenv("FINNHUB_API_KEY", "")
        self._finnhub_consecutive_failures = 0
        self._finnhub_failure_threshold = 5  # configurable
        self._finnhub_disabled_for_session = False
        self.base_url = "https://finnhub.io/api/v1"

    def _check_disabled(self) -> bool:
        if self._finnhub_disabled_for_session:
            logger.error(f"Finnhub API disabled for this session after {self._finnhub_failure_threshold} consecutive failures. Skipping all Finnhub requests.")
            return True
        if not self.api_key or self.api_key == "DUMMY":
            logger.warning("No Finnhub API key available. Skipping Finnhub requests.")
            return True
        return False

    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get real-time quote data for a symbol."""
        if self._check_disabled():
            return None
        try:
            url = f"{self.base_url}/quote"
            params = {"symbol": symbol, "token": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
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
            logger.error(f"Finnhub quote fetch failed for {symbol}: {str(e)}")
            return None

    def get_company_profile(self, symbol: str) -> Optional[Dict]:
        """Get company profile for a symbol."""
        if self._check_disabled():
            return None
        try:
            url = f"{self.base_url}/stock/profile2"
            params = {"symbol": symbol, "token": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
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
            logger.error(f"Finnhub profile fetch failed for {symbol}: {str(e)}")
            return None

    def get_news(self, symbol: str, from_date: str = None, to_date: str = None) -> List[Dict]:
        """Get company-specific news from Finnhub."""
        if self._check_disabled():
            return []
        try:
            url = f"{self.base_url}/company-news"
            params = {"symbol": symbol, "token": self.api_key}
            if from_date:
                params["from"] = from_date
            if to_date:
                params["to"] = to_date
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
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
            logger.error(f"Finnhub news fetch failed for {symbol}: {str(e)}")
            return []

    # Additional endpoints (sentiment, earnings, etc.) can be added here following the same pattern.

# Global instance
finnhub_data_collector = FinnhubDataCollector()
