"""
Unified data collector for Market Voices
Manages multiple data sources with fallback logic
"""
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from loguru import logger
import os
import yfinance as yf

from ..config.settings import get_settings
from .fmp_stock_data import fmp_stock_collector
from .news_collector import news_collector


class UnifiedDataCollector:
    """Unified data collector with multiple source fallback"""
    
    def __init__(self):
        self.settings = get_settings()
        self.sources = [
            ("FMP", self._collect_fmp_data),
            ("Yahoo Finance", self._collect_yf_data),
            ("Alpha Vantage", self._collect_av_data)
        ]
        
    def _collect_fmp_data(self, symbols: List[str]) -> Tuple[bool, List[Dict], str]:
        """Collect data from FMP API"""
        try:
            logger.info("Attempting to collect data from FMP API...")
            
            # Use FMP collector with provided symbols
            original_symbols = fmp_stock_collector.symbols
            fmp_stock_collector.symbols = symbols
            
            stock_data = fmp_stock_collector.collect_data()
            
            if stock_data:
                # Analyze market sentiment
                market_sentiment = fmp_stock_collector.analyze_market_sentiment(stock_data)
                
                # Get news data
                news_data = news_collector.get_market_news(
                    symbols=[stock['symbol'] for stock in stock_data], 
                    stock_data=stock_data
                )
                
                # Add news summaries to stock data
                for stock in stock_data:
                    symbol = stock['symbol']
                    if symbol in news_data.get('news_summaries', {}):
                        stock['news_summary'] = news_data['news_summaries'][symbol]
                
                logger.info(f"FMP collection successful: {len(stock_data)} stocks")
                return True, stock_data, "FMP API"
            else:
                logger.warning("FMP collection returned no data")
                return False, [], "FMP API - No data"
                
        except Exception as e:
            logger.error(f"FMP collection failed: {str(e)}")
            return False, [], f"FMP API - {str(e)}"
    
    def _collect_yf_data(self, symbols: List[str]) -> Tuple[bool, List[Dict], str]:
        """Collect data from Yahoo Finance (fallback)"""
        try:
            logger.info("Attempting to collect data from Yahoo Finance...")
            
            # Use yfinance for basic data collection
            all_data = []
            
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    
                    # Get current day's data
                    hist = ticker.history(period="2d")
                    
                    if len(hist) < 2:
                        logger.warning(f"Insufficient data for {symbol}")
                        continue
                    
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
                    
                    stock_data = {
                        'symbol': symbol,
                        'company_name': company_name,
                        'current_price': round(current_price, 2),
                        'previous_price': round(previous_price, 2),
                        'price_change': round(price_change, 2),
                        'percent_change': round(percent_change, 2),
                        'current_volume': current_volume,
                        'average_volume': avg_volume,
                        'volume_ratio': round(current_volume / avg_volume, 2) if avg_volume > 0 else 1.0,
                        'market_cap': info.get('marketCap', 0),
                        'rsi': 50.0,  # Default neutral RSI
                        'macd_signal': None,
                        'technical_signals': [],
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    all_data.append(stock_data)
                    
                    # Small delay to be respectful
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch {symbol} from Yahoo Finance: {str(e)}")
                    continue
            
            if all_data:
                # Get basic news data
                news_data = news_collector.get_market_news(
                    symbols=[stock['symbol'] for stock in all_data]
                )
                
                # Add news summaries
                for stock in all_data:
                    symbol = stock['symbol']
                    if symbol in news_data.get('news_summaries', {}):
                        stock['news_summary'] = news_data['news_summaries'][symbol]
                
                logger.info(f"Yahoo Finance collection successful: {len(all_data)} stocks")
                return True, all_data, "Yahoo Finance"
            else:
                logger.warning("Yahoo Finance collection returned no data")
                return False, [], "Yahoo Finance - No data"
                
        except Exception as e:
            logger.error(f"Yahoo Finance collection failed: {str(e)}")
            return False, [], f"Yahoo Finance - {str(e)}"
    
    def _collect_av_data(self, symbols: List[str]) -> Tuple[bool, List[Dict], str]:
        """Collect data from Alpha Vantage (third fallback)"""
        try:
            logger.info("Attempting to collect data from Alpha Vantage...")
            
            # Check if we have Alpha Vantage API key
            av_api_key = self.settings.alpha_vantage_api_key
            if not av_api_key or av_api_key == "DUMMY":
                logger.warning("No Alpha Vantage API key available")
                return False, [], "Alpha Vantage - No API key"
            
            import requests
            
            all_data = []
            base_url = "https://www.alphavantage.co/query"
            
            for symbol in symbols:
                try:
                    # Get quote endpoint
                    params = {
                        'function': 'GLOBAL_QUOTE',
                        'symbol': symbol,
                        'apikey': av_api_key
                    }
                    
                    response = requests.get(base_url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    quote = data.get('Global Quote', {})
                    if not quote:
                        logger.warning(f"No quote data for {symbol}")
                        continue
                    
                    # Parse quote data
                    current_price = float(quote.get('05. price', 0))
                    previous_price = float(quote.get('08. previous close', current_price))
                    price_change = float(quote.get('09. change', 0))
                    percent_change = float(quote.get('10. change percent', '0%').replace('%', ''))
                    volume = int(quote.get('06. volume', 0))
                    
                    # Get company overview for additional data
                    overview_params = {
                        'function': 'OVERVIEW',
                        'symbol': symbol,
                        'apikey': av_api_key
                    }
                    
                    overview_response = requests.get(base_url, params=overview_params, timeout=10)
                    overview_data = overview_response.json() if overview_response.status_code == 200 else {}
                    
                    company_name = overview_data.get('Name', symbol)
                    market_cap = float(overview_data.get('MarketCapitalization', 0))
                    
                    stock_data = {
                        'symbol': symbol,
                        'company_name': company_name,
                        'current_price': round(current_price, 2),
                        'previous_price': round(previous_price, 2),
                        'price_change': round(price_change, 2),
                        'percent_change': round(percent_change, 2),
                        'current_volume': volume,
                        'average_volume': volume,  # Alpha Vantage doesn't provide avg volume easily
                        'volume_ratio': 1.0,  # Default since we don't have avg volume
                        'market_cap': market_cap,
                        'rsi': 50.0,  # Default neutral RSI
                        'macd_signal': None,
                        'technical_signals': [],
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    all_data.append(stock_data)
                    
                    # Alpha Vantage has strict rate limits (5 calls per minute for free tier)
                    time.sleep(12)  # Wait 12 seconds between calls to stay under limit
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch {symbol} from Alpha Vantage: {str(e)}")
                    continue
            
            if all_data:
                # Get basic news data
                news_data = news_collector.get_market_news(
                    symbols=[stock['symbol'] for stock in all_data]
                )
                
                # Add news summaries
                for stock in all_data:
                    symbol = stock['symbol']
                    if symbol in news_data.get('news_summaries', {}):
                        stock['news_summary'] = news_data['news_summaries'][symbol]
                
                logger.info(f"Alpha Vantage collection successful: {len(all_data)} stocks")
                return True, all_data, "Alpha Vantage"
            else:
                logger.warning("Alpha Vantage collection returned no data")
                return False, [], "Alpha Vantage - No data"
                
        except Exception as e:
            logger.error(f"Alpha Vantage collection failed: {str(e)}")
            return False, [], f"Alpha Vantage - {str(e)}"
    
    def _create_cached_data(self, symbols: List[str]) -> List[Dict]:
        """Create data from cached sources or minimal web scraping (fourth fallback)"""
        logger.warning("Using cached/minimal data as fourth fallback")
        
        # This would implement a more sophisticated fallback
        # For now, we'll use a simple approach that doesn't rely on APIs
        cached_data = []
        
        for i, symbol in enumerate(symbols):
            # Create basic data structure that could be populated from cache
            # or minimal web scraping in a real implementation
            cached_stock = {
                'symbol': symbol,
                'company_name': f'{symbol} Corporation',  # Would be from cache
                'current_price': 100.0 + (i * 5),  # Would be from cache
                'previous_price': 100.0 + (i * 5) - 1.0,  # Would be from cache
                'price_change': 1.0 if i % 2 == 0 else -0.5,  # Would be from cache
                'percent_change': 1.0 if i % 2 == 0 else -0.5,  # Would be from cache
                'current_volume': 1000000,  # Would be from cache
                'average_volume': 1000000,  # Would be from cache
                'volume_ratio': 1.0,  # Would be from cache
                'market_cap': 1000000000,  # Would be from cache
                'rsi': 50.0,  # Would be from cache
                'macd_signal': None,  # Would be from cache
                'technical_signals': [],  # Would be from cache
                'timestamp': datetime.now().isoformat(),
                'data_source': 'Cached/Minimal'
            }
            cached_data.append(cached_stock)
        
        return cached_data
    
    def collect_data(self, symbols: List[str] = None, production_mode: bool = True) -> Dict:
        """Collect data from multiple sources with fallback"""
        logger.info("Starting unified data collection with fallback")
        
        # Use provided symbols or get from FMP
        if symbols is None:
            symbols = fmp_stock_collector.symbols[:20]  # Limit for rate limit management
        
        logger.info(f"Collecting data for {len(symbols)} symbols")
        
        # Try each source in order
        for source_name, source_func in self.sources:
            success, data, message = source_func(symbols)
            
            if success and data:
                # Sort by percent change
                data.sort(key=lambda x: x.get('percent_change', 0), reverse=True)
                
                # Get top winners and losers
                winners = [stock for stock in data if stock.get('percent_change', 0) > 0][:5]
                losers = [stock for stock in data if stock.get('percent_change', 0) < 0][:5]
                
                # Create market summary
                market_summary = {
                    'total_stocks': len(data),
                    'advancing_stocks': len([s for s in data if s.get('percent_change', 0) > 0]),
                    'declining_stocks': len([s for s in data if s.get('percent_change', 0) < 0]),
                    'average_change': sum(s.get('percent_change', 0) for s in data) / len(data),
                    'market_sentiment': 'Mixed',  # Default sentiment
                    'market_date': datetime.now().isoformat(),
                    'collection_timestamp': datetime.now().isoformat(),
                    'data_source': source_name
                }
                
                # Try to get market sentiment if available
                if source_name == "FMP":
                    try:
                        sentiment = fmp_stock_collector.analyze_market_sentiment(data)
                        market_summary['market_sentiment'] = sentiment.get('market_sentiment', 'Mixed')
                    except:
                        pass
                
                result = {
                    'market_summary': market_summary,
                    'winners': winners,
                    'losers': losers,
                    'all_data': data,
                    'collection_success': True,
                    'data_source': source_name,
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"Data collection successful using {source_name}")
                return result
        
        # If all sources fail, handle based on production mode
        if production_mode:
            logger.error("All data sources failed in production mode")
            return {
                'collection_success': False,
                'error': 'All data sources failed - cannot generate production content without real data',
                'data_source': 'Failed',
                'timestamp': datetime.now().isoformat()
            }
        else:
            # Only use cached/mock data in test mode
            logger.warning("All data sources failed, using cached data (test mode only)")
            cached_data = self._create_cached_data(symbols[:10])  # Use fewer symbols for cached data
            
            # Sort cached data
            cached_data.sort(key=lambda x: x.get('percent_change', 0), reverse=True)
            winners = [stock for stock in cached_data if stock.get('percent_change', 0) > 0][:5]
            losers = [stock for stock in cached_data if stock.get('percent_change', 0) < 0][:5]
            
            market_summary = {
                'total_stocks': len(cached_data),
                'advancing_stocks': len([s for s in cached_data if s.get('percent_change', 0) > 0]),
                'declining_stocks': len([s for s in cached_data if s.get('percent_change', 0) < 0]),
                'average_change': sum(s.get('percent_change', 0) for s in cached_data) / len(cached_data),
                'market_sentiment': 'Test Data',
                'market_date': datetime.now().isoformat(),
                'collection_timestamp': datetime.now().isoformat(),
                'data_source': 'Cached/Test Data'
            }
            
            return {
                'market_summary': market_summary,
                'winners': winners,
                'losers': losers,
                'all_data': cached_data,
                'collection_success': True,
                'data_source': 'Cached/Test Data',
                'timestamp': datetime.now().isoformat()
            }


# Global instance
unified_collector = UnifiedDataCollector() 