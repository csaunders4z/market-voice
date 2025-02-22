"""
Financial Modeling Prep data source implementation
"""

import os
import requests
import logging
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import MarketDataSource

class FMPDataSource(MarketDataSource):
    """Financial Modeling Prep API implementation"""
    
    def __init__(self):
        super().__init__("FMP")
        self.api_key = os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("FMP_API_KEY environment variable not set")
        self.base_url = "https://financialmodelingprep.com/api/v3"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_request(self, endpoint: str, params: Dict = None) -> Any:
        """Make request to FMP API with retry logic"""
        try:
            params = params or {}
            params['apikey'] = self.api_key
            
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                raise ValueError(f"Empty response from FMP for {endpoint}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logging.error(f"FMP API request failed for {endpoint}: {str(e)}")
            raise
        except ValueError as e:
            logging.error(f"FMP API invalid response for {endpoint}: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in FMP API request: {str(e)}")
            raise

    def get_quote(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get current quote data from FMP"""
        try:
            data = self._make_request(f"quote/{ticker}")
            if data and len(data) > 0:
                quote = data[0]
                return {
                    'price': quote.get('price', 0),
                    'change': quote.get('change', 0),
                    'change_percent': quote.get('changesPercentage', 0),
                    'volume': quote.get('volume', 0),
                    'avg_volume': quote.get('avgVolume', 0)
                }
            return None
        except Exception as e:
            logging.warning(f"FMP quote error for {ticker}: {str(e)}")
            return None

    def get_profile(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get company profile data from FMP"""
        try:
            data = self._make_request(f"profile/{ticker}")
            if data and len(data) > 0:
                profile = data[0]
                return {
                    'name': profile.get('companyName', ticker),
                    'sector': profile.get('sector', ''),
                    'industry': profile.get('industry', ''),
                    'market_cap': profile.get('mktCap', 0)
                }
            return None
        except Exception as e:
            logging.warning(f"FMP profile error for {ticker}: {str(e)}")
            return None

    def get_news(self, ticker: str) -> Optional[str]:
        """Get recent news from FMP"""
        try:
            news = self._make_request("stock_news", {"tickers": ticker, "limit": 2})
            if news:
                return "; ".join(
                    f"{item['title']} ({item['site']})" 
                    for item in news[:2]
                )
            return None
        except Exception as e:
            logging.warning(f"FMP news error for {ticker}: {str(e)}")
            return None