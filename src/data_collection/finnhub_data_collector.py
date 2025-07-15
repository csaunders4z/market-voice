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
        self._finnhub_failure_threshold = 3  # Reduced from 5 for faster circuit breaking
        self._finnhub_disabled_for_session = False
        self._disabled_until = None
        self._recovery_delay = 300  # 5 minutes recovery delay
        self.base_url = "https://finnhub.io/api/v1"

    def _check_disabled(self) -> bool:
        if self._disabled_until and time.time() > self._disabled_until:
            logger.info("Finnhub API recovery period elapsed, re-enabling with reduced rate")
            self._finnhub_disabled_for_session = False
            self._finnhub_consecutive_failures = 0
            self._disabled_until = None
            return False
        
        if self._finnhub_disabled_for_session:
            remaining = int(self._disabled_until - time.time()) if self._disabled_until else 0
            logger.error(f"Finnhub API disabled for {remaining}s after {self._finnhub_failure_threshold} consecutive failures. Skipping request.")
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
            response = requests.get(url, params=params, timeout=15)  # Increased timeout
            
            if response.status_code == 200:
                data = response.json()
                if not data or "c" not in data:
                    logger.warning(f"No quote data for {symbol} from Finnhub.")
                    self._handle_failure(f"No quote data for {symbol}")
                    return None
                self._finnhub_consecutive_failures = 0  # Reset on success
                return {
                    "symbol": symbol,
                    "current_price": data.get("c"),
                    "high": data.get("h"),
                    "low": data.get("l"),
                    "open": data.get("o"),
                    "previous_close": data.get("pc"),
                    "timestamp": datetime.fromtimestamp(data.get("t", 0)).isoformat() if data.get("t") else None
                }
            elif response.status_code == 422:
                logger.warning(f"Finnhub 422 error for {symbol} - symbol may not be supported")
                return None
            elif response.status_code == 429:
                error_msg = f"Finnhub rate limited for {symbol}: {response.status_code}"
                logger.warning(error_msg)
                self._handle_failure(error_msg)
                time.sleep(2)  # Wait before next request
                return None
            else:
                error_msg = f"Finnhub quote fetch failed for {symbol}: {response.status_code} {response.reason}"
                logger.error(error_msg)
                self._handle_failure(error_msg)
                return None
                
        except Exception as e:
            error_msg = f"Finnhub quote fetch exception for {symbol}: {str(e)}"
            logger.error(error_msg)
            self._handle_failure(error_msg)
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

    def _handle_failure(self, error_msg: str):
        """Handle API failure and implement circuit breaker with recovery."""
        self._finnhub_consecutive_failures += 1
        if self._finnhub_consecutive_failures >= self._finnhub_failure_threshold:
            self._finnhub_disabled_for_session = True
            self._disabled_until = time.time() + self._recovery_delay
            logger.error(f"Finnhub API disabled for {self._recovery_delay}s after {self._finnhub_failure_threshold} consecutive failures: {error_msg}")
        else:
            logger.warning(f"Finnhub failure {self._finnhub_consecutive_failures}/{self._finnhub_failure_threshold}: {error_msg}")

    # Additional endpoints (sentiment, earnings, etc.) can be added here following the same pattern.

# Global instance
finnhub_data_collector = FinnhubDataCollector()
