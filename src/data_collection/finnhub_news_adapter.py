"""
Finnhub News Adapter for Market Voice
Provides company-specific news and sentiment with global circuit breaker/session disable logic.
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger
import requests
import pytz

from src.config.settings import get_settings

class FinnhubNewsAdapter:
    """Fetches company news and sentiment from Finnhub with circuit breaker/session disable logic."""
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.finnhub_api_key or os.getenv("FINNHUB_API_KEY", "")
        self.market_tz = pytz.timezone('US/Eastern')
        self._finnhub_news_consecutive_failures = 0
        self._finnhub_news_failure_threshold = 5
        self._finnhub_news_disabled_for_session = False
        self.base_url = "https://finnhub.io/api/v1"

    def _check_disabled(self) -> bool:
        if self._finnhub_news_disabled_for_session:
            logger.error(f"Finnhub News API disabled for this session after {self._finnhub_news_failure_threshold} consecutive failures. Skipping all Finnhub news requests.")
            return True
        if not self.api_key or self.api_key == "DUMMY":
            logger.warning("No Finnhub API key available. Skipping Finnhub news requests.")
            return True
        return False

    def get_company_news(self, symbol: str, from_date: Optional[str] = None, to_date: Optional[str] = None, limit: int = 8) -> List[Dict]:
        """Get company-specific news from Finnhub."""
        if self._check_disabled():
            return []
        try:
            url = f"{self.base_url}/company-news"
            if not from_date:
                market_now = datetime.now(self.market_tz)
                from_date = (market_now - timedelta(days=2)).strftime('%Y-%m-%d')
            if not to_date:
                market_now = datetime.now(self.market_tz)
                to_date = market_now.strftime('%Y-%m-%d')
            params = {"symbol": symbol, "from": from_date, "to": to_date, "token": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not data or not isinstance(data, list):
                logger.warning(f"No news data for {symbol} from Finnhub.")
                self._finnhub_news_consecutive_failures += 1
                if self._finnhub_news_consecutive_failures >= self._finnhub_news_failure_threshold:
                    self._finnhub_news_disabled_for_session = True
                    logger.error(f"Finnhub News API disabled for the remainder of this session after {self._finnhub_news_failure_threshold} consecutive failures.")
                return []
            self._finnhub_news_consecutive_failures = 0
            # Sort by datetime, filter today's articles in market timezone
            market_now = datetime.now(self.market_tz)
            today_market = market_now.date()
            today_articles = []
            
            for article in data:
                timestamp = article.get("datetime", 0)
                if timestamp:
                    article_date = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
                    article_date_market = article_date.astimezone(self.market_tz)
                    
                    if article_date_market.date() == today_market:
                        today_articles.append({
                            "title": article.get("headline"),
                            "description": article.get("summary"),
                            "url": article.get("url"),
                            "source": article.get("source"),
                            "published_at": article.get("datetime"),
                            "relevance_score": 8.0
                        })
            return today_articles[:limit]
        except Exception as e:
            self._finnhub_news_consecutive_failures += 1
            if self._finnhub_news_consecutive_failures >= self._finnhub_news_failure_threshold:
                self._finnhub_news_disabled_for_session = True
                logger.error(f"Finnhub News API disabled for the remainder of this session after {self._finnhub_news_failure_threshold} consecutive failures (exception path).")
            logger.error(f"Finnhub news fetch failed for {symbol}: {str(e)}")
            return []

    def get_news_sentiment(self, symbol: str) -> Dict:
        """Get news sentiment for a company from Finnhub."""
        if self._check_disabled():
            return {}
        try:
            url = f"{self.base_url}/news-sentiment"
            params = {"symbol": symbol, "token": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not data or "companyNewsScore" not in data:
                logger.warning(f"No sentiment data for {symbol} from Finnhub.")
                self._finnhub_news_consecutive_failures += 1
                if self._finnhub_news_consecutive_failures >= self._finnhub_news_failure_threshold:
                    self._finnhub_news_disabled_for_session = True
                    logger.error(f"Finnhub News API disabled for the remainder of this session after {self._finnhub_news_failure_threshold} consecutive failures.")
                return {}
            self._finnhub_news_consecutive_failures = 0
            return data
        except Exception as e:
            self._finnhub_news_consecutive_failures += 1
            if self._finnhub_news_consecutive_failures >= self._finnhub_news_failure_threshold:
                self._finnhub_news_disabled_for_session = True
                logger.error(f"Finnhub News API disabled for the remainder of this session after {self._finnhub_news_failure_threshold} consecutive failures (exception path).")
            logger.error(f"Finnhub news sentiment fetch failed for {symbol}: {str(e)}")
            return {}

# Global instance
finnhub_news_adapter = FinnhubNewsAdapter()
