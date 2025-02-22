"""
Finnhub data source implementation
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import MarketDataSource

class FinnhubDataSource(MarketDataSource):
    """Finnhub API implementation"""
    
    def __init__(self):
        super().__init__("Finnhub")
        self.api_key = os.getenv('FINNHUB_API_KEY')
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY environment variable not set")
        self.base_url = "https://finnhub.io/api/v1"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_request(self, endpoint: str, params: Dict = None) -> Any:
        """Make request to Finnhub API with retry logic"""
        try:
            params = params or {}
            headers = {'X-Finnhub-Token': self.api_key}
            
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                raise ValueError(f"Empty response from Finnhub for {endpoint}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Finnhub API request failed for {endpoint}: {str(e)}")
            raise
        except ValueError as e:
            logging.error(f"Finnhub API invalid response for {endpoint}: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in Finnhub API request: {str(e)}")
            raise

    def get_quote(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get current quote data from Finnhub"""
        try:
            data = self._make_request('quote', {'symbol': ticker})
            if data and 'c' in data:  # 'c' is current price
                return {
                    'price': data.get('c', 0),  # Current price
                    'change': data.get('d', 0),  # Change
                    'change_percent': data.get('dp', 0),  # Percent change
                    'volume': data.get('v', 0),  # Current volume
                    'avg_volume': 0  # Not available in basic quote
                }
            return None
        except Exception as e:
            logging.warning(f"Finnhub quote error for {ticker}: {str(e)}")
            return None

    def get_profile(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get company profile data from Finnhub"""
        try:
            data = self._make_request('stock/profile2', {'symbol': ticker})
            if data:
                return {
                    'name': data.get('name', ticker),
                    'sector': data.get('finnhubIndustry', ''),  # Finnhub uses different categorization
                    'industry': data.get('finnhubIndustry', ''),
                    'market_cap': data.get('marketCapitalization', 0) * 1_000_000  # Convert to actual value
                }
            return None
        except Exception as e:
            logging.warning(f"Finnhub profile error for {ticker}: {str(e)}")
            return None

    def get_news(self, ticker: str) -> Optional[str]:
        """Get recent news from Finnhub"""
        try:
            # Get news from last 24 hours
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            news = self._make_request('company-news', {
                'symbol': ticker,
                'from': start_date,
                'to': end_date
            })
            
            if news:
                # Filter for relevant news and format
                formatted_news = []
                for item in news[:2]:  # Take top 2 news items
                    headline = item.get('headline', '')
                    source = item.get('source', 'Unknown')
                    formatted_news.append(f"{headline} ({source})")
                
                return "; ".join(formatted_news) if formatted_news else None
                
            return None
        except Exception as e:
            logging.warning(f"Finnhub news error for {ticker}: {str(e)}")
            return None