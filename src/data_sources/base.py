"""
Base class for market data sources
"""

from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

class MarketDataSource:
    """Base class defining interface for all market data sources"""
    
    def __init__(self, name: str):
        self.name = name
    
    def get_quote(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get quote data for a ticker
        Returns dict with keys: price, change, change_percent, volume, avg_volume
        """
        raise NotImplementedError
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_profile(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get company profile data
        Returns dict with keys: name, sector, industry, market_cap
        """
        raise NotImplementedError
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_news(self, ticker: str) -> Optional[str]:
        """
        Get news for a ticker
        Returns formatted string with latest news items
        """
        raise NotImplementedError

    def get_stock_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get all available data for a ticker
        Returns combined dictionary of quote, profile, and news data
        """
        try:
            # Get quote data
            stock_data = self.get_quote(ticker)
            if not stock_data:
                return None
            
            # Add profile data
            profile = self.get_profile(ticker)
            if profile:
                stock_data.update(profile)
            
            # Add news if significant price movement
            if abs(stock_data.get('change_percent', 0)) > 2:
                news = self.get_news(ticker)
                if news:
                    stock_data['news'] = news
            
            return stock_data
            
        except Exception as e:
            print(f"Error getting data for {ticker} from {self.name}: {str(e)}")
            return None