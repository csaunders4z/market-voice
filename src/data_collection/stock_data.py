"""
Stock data collection for Market Voices
Handles NASDAQ-100 data fetching and analysis
"""
import yfinance as yf
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import pytz
from loguru import logger
import time
import random
import os

from ..config.settings import get_settings
from .fmp_stock_data import fmp_stock_collector
from .news_collector import news_collector
from .unified_data_collector import unified_collector


class StockDataCollector:
    """Collects and analyzes stock market data for NASDAQ-100"""
    
    def __init__(self):
        self.symbols = get_settings().nasdaq_100_symbols
        self.est_tz = pytz.timezone('US/Eastern')
        self.data_cache = {}
        
    def is_market_open(self) -> bool:
        """Check if the market is currently open"""
        now = datetime.now(self.est_tz)
        current_time = now.time()
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
            
        # Check if it's within market hours
        return get_settings().market_open_time <= current_time <= get_settings().market_close_time
    
    def get_market_date(self) -> datetime:
        """Get the most recent market date"""
        now = datetime.now(self.est_tz)
        
        # If market is closed, use today's date
        # If market is open, use today's date
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def fetch_stock_data(self, symbol: str) -> Optional[Dict]:
        """Fetch data for a single stock symbol"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current day's data
            hist = ticker.history(period="2d")
            
            if len(hist) < 2:
                logger.warning(f"Insufficient data for {symbol}")
                return None
            
            # Calculate daily change
            current_price = hist['Close'].iloc[-1]
            previous_price = hist['Close'].iloc[-2]
            price_change = current_price - previous_price
            percent_change = (price_change / previous_price) * 100
            
            # Get volume data
            current_volume = hist['Volume'].iloc[-1]
            avg_volume = ticker.info.get('averageVolume', current_volume)
            
            # Get company info
            info = ticker.info
            company_name = info.get('longName', symbol)
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            
            return {
                'symbol': symbol,
                'company_name': company_name,
                'current_price': round(current_price, 2),
                'previous_price': round(previous_price, 2),
                'price_change': round(price_change, 2),
                'percent_change': round(percent_change, 2),
                'current_volume': current_volume,
                'average_volume': avg_volume,
                'volume_ratio': round(current_volume / avg_volume, 2) if avg_volume > 0 else 1.0,
                'sector': sector,
                'industry': industry,
                'market_cap': info.get('marketCap', 0),
                'timestamp': datetime.now(self.est_tz)
            }
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def collect_nasdaq_data(self) -> pd.DataFrame:
        """Collect data for all NASDAQ-100 symbols"""
        logger.info("Starting NASDAQ-100 data collection")
        
        all_data = []
        successful_fetches = 0
        
        for i, symbol in enumerate(self.symbols):
            logger.debug(f"Fetching data for {symbol} ({i+1}/{len(self.symbols)})")
            
            data = self.fetch_stock_data(symbol)
            if data:
                all_data.append(data)
                successful_fetches += 1
            
            # Rate limiting to avoid API issues
            if i % 10 == 0 and i > 0:
                time.sleep(1)
        
        logger.info(f"Successfully collected data for {successful_fetches}/{len(self.symbols)} symbols")
        
        if not all_data:
            raise ValueError("No stock data collected")
        
        df = pd.DataFrame(all_data)
        df = df.sort_values('percent_change', ascending=False)
        
        return df
    
    def collect_enhanced_data(self) -> Dict:
        """Collect enhanced data using unified collector with fallback"""
        logger.info("Starting enhanced data collection with unified collector")
        
        try:
            # Determine if we're in production mode
            production_mode = os.getenv("TEST_MODE") != "1"
            
            # Use unified collector with fallback logic
            market_data = unified_collector.collect_data(production_mode=production_mode)
            
            if not market_data.get('collection_success'):
                logger.error("Unified data collection failed")
                return {'collection_success': False, 'error': 'Unified collection failed'}
            
            logger.info(f"Enhanced collection completed using {market_data.get('data_source', 'Unknown')}")
            logger.info(f"Stocks: {len(market_data.get('all_data', []))}, "
                       f"Winners: {len(market_data.get('winners', []))}, "
                       f"Losers: {len(market_data.get('losers', []))}")
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error in enhanced data collection: {str(e)}")
            return {
                'collection_success': False,
                'error': str(e),
                'timestamp': datetime.now(self.est_tz).isoformat()
            }
    
    def get_top_movers(self, df: pd.DataFrame, top_count: int = 5) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get top winners and losers"""
        winners = df.head(top_count).copy()
        losers = df.tail(top_count).copy()
        
        return winners, losers
    
    def identify_significant_movers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identify stocks with significant price movements"""
        threshold = get_settings().significant_move_threshold
        
        significant = df[
            (df['percent_change'].abs() >= threshold) |
            (df['volume_ratio'] >= get_settings().volume_threshold_multiplier)
        ].copy()
        
        return significant
    
    def get_market_summary(self, df: pd.DataFrame) -> Dict:
        """Generate market summary statistics"""
        summary = {
            'total_stocks': len(df),
            'advancing_stocks': len(df[df['percent_change'] > 0]),
            'declining_stocks': len(df[df['percent_change'] < 0]),
            'unchanged_stocks': len(df[df['percent_change'] == 0]),
            'average_change': df['percent_change'].mean(),
            'median_change': df['percent_change'].median(),
            'total_volume': df['current_volume'].sum(),
            'market_date': self.get_market_date(),
            'collection_timestamp': datetime.now(self.est_tz)
        }
        
        return summary
    
    def run_daily_collection(self) -> Dict:
        """Main method to run daily data collection with enhanced features"""
        logger.info("Starting daily market data collection with enhanced features")
        
        # Use enhanced collection by default
        return self.collect_enhanced_data()


# Global instance
stock_collector = StockDataCollector() 