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
from ..utils.rate_limiter import api_rate_limiter, rate_limiter
from .fmp_stock_data import fmp_stock_collector
from .news_collector import news_collector
from .economic_calendar import economic_calendar
from .free_news_sources import free_news_collector


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
        """Collect data from FMP API with rate limiting"""
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
        finally:
            # Restore original symbols
            fmp_stock_collector.symbols = original_symbols
    
    def _collect_yf_data(self, symbols: List[str]) -> Tuple[bool, List[Dict], str]:
        """Collect data from Yahoo Finance with rate limiting and enhanced data"""
        try:
            logger.info("Attempting to collect data from Yahoo Finance...")
            
            all_data = []
            
            # Use batch processing for Yahoo Finance
            def fetch_yahoo_stock(symbol: str) -> Optional[Dict]:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    # Get current price data
                    hist = ticker.history(period="2d")
                    if len(hist) < 2:
                        return None
                    
                    current_price = hist['Close'].iloc[-1]
                    previous_price = hist['Close'].iloc[-2]
                    price_change = current_price - previous_price
                    percent_change = (price_change / previous_price) * 100
                    
                    current_volume = hist['Volume'].iloc[-1]
                    avg_volume = info.get('averageVolume', current_volume)
                    
                    company_name = info.get('longName', symbol)
                    
                    # Get earnings calendar data
                    earnings_data = None
                    try:
                        calendar = ticker.calendar
                        if calendar is not None and hasattr(calendar, 'empty') and not calendar.empty:
                            next_earnings = calendar.iloc[0] if len(calendar) > 0 else None
                            if next_earnings is not None:
                                earnings_data = {
                                    'date': next_earnings.get('Earnings Date', ''),
                                    'estimate': next_earnings.get('EPS Estimate', None),
                                    'actual': next_earnings.get('EPS Actual', None),
                                    'revenue_estimate': next_earnings.get('Revenue Estimate', None),
                                    'revenue_actual': next_earnings.get('Revenue Actual', None)
                                }
                    except Exception as e:
                        logger.debug(f"Could not fetch earnings calendar for {symbol}: {str(e)}")
                    
                    # Get analyst recommendations
                    analyst_data = None
                    try:
                        recommendations = ticker.recommendations
                        if recommendations is not None and hasattr(recommendations, 'empty') and not recommendations.empty:
                            recent_recs = recommendations.tail(5)  # Last 5 recommendations
                            if not recent_recs.empty:
                                # Count recommendations
                                rec_counts = recent_recs['To Grade'].value_counts()
                                buy_count = rec_counts.get('Buy', 0) + rec_counts.get('Strong Buy', 0)
                                hold_count = rec_counts.get('Hold', 0)
                                sell_count = rec_counts.get('Sell', 0) + rec_counts.get('Strong Sell', 0)
                                
                                # Determine consensus
                                total = buy_count + hold_count + sell_count
                                if total > 0:
                                    if buy_count > hold_count and buy_count > sell_count:
                                        consensus = 'buy'
                                    elif sell_count > hold_count and sell_count > buy_count:
                                        consensus = 'sell'
                                    else:
                                        consensus = 'hold'
                                else:
                                    consensus = 'hold'
                                
                                analyst_data = {
                                    'consensus': consensus,
                                    'ratings_count': {
                                        'buy': buy_count,
                                        'hold': hold_count,
                                        'sell': sell_count
                                    },
                                    'recent_recommendations': recent_recs.tail(3).to_dict('records') if len(recent_recs) >= 3 else recent_recs.to_dict('records')
                                }
                    except Exception as e:
                        logger.debug(f"Could not fetch analyst recommendations for {symbol}: {str(e)}")
                    
                    # Get price targets
                    price_target = None
                    try:
                        price_target = info.get('targetMeanPrice')
                    except:
                        pass
                    
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
                        'earnings_data': earnings_data,
                        'analyst_data': analyst_data,
                        'price_target': price_target,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    return stock_data
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch {symbol} from Yahoo Finance: {str(e)}")
                    return None
            
            # Process symbols in batches with rate limiting
            all_data = rate_limiter.batch_process(
                items=symbols,
                batch_size=self.settings.yahoo_batch_size,
                batch_delay=self.settings.yahoo_batch_delay,
                process_func=fetch_yahoo_stock,
                api_name="Yahoo Finance"
            )
            
            if all_data:
                logger.info(f"Yahoo Finance collection successful: {len(all_data)} stocks")
                return True, all_data, "Yahoo Finance"
            else:
                logger.warning("Yahoo Finance collection returned no data")
                return False, [], "Yahoo Finance - No data"
                
        except Exception as e:
            logger.error(f"Yahoo Finance collection failed: {str(e)}")
            return False, [], f"Yahoo Finance - {str(e)}"
    
    def _collect_av_data(self, symbols: List[str]) -> Tuple[bool, List[Dict], str]:
        """Collect data from Alpha Vantage with rate limiting"""
        try:
            logger.info("Attempting to collect data from Alpha Vantage...")
            
            # Check if we have Alpha Vantage API key
            av_api_key = self.settings.alpha_vantage_api_key
            if not av_api_key or av_api_key == "DUMMY":
                logger.warning("No Alpha Vantage API key available")
                return False, [], "Alpha Vantage - No API key"
            
            import requests
            
            def fetch_av_stock(symbol: str) -> Optional[Dict]:
                try:
                    base_url = "https://www.alphavantage.co/query"
                    
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
                        return None
                    
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
                    
                    return stock_data
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch {symbol} from Alpha Vantage: {str(e)}")
                    return None
            
            # Process symbols in batches with strict rate limiting for Alpha Vantage
            all_data = rate_limiter.batch_process(
                items=symbols,
                batch_size=self.settings.alpha_vantage_batch_size,
                batch_delay=self.settings.alpha_vantage_batch_delay,
                process_func=fetch_av_stock,
                api_name="Alpha Vantage"
            )
            
            if all_data:
                logger.info(f"Alpha Vantage collection successful: {len(all_data)} stocks")
                return True, all_data, "Alpha Vantage"
            else:
                logger.warning("Alpha Vantage collection returned no data")
                return False, [], "Alpha Vantage - No data"
                
        except Exception as e:
            logger.error(f"Alpha Vantage collection failed: {str(e)}")
            return False, [], f"Alpha Vantage - {str(e)}"
    
    def _create_cached_data(self, symbols: List[str]) -> List[Dict]:
        """Create cached/mock data for testing"""
        cached_data = []
        for i, symbol in enumerate(symbols):
            # Create realistic mock data
            base_price = 100 + (i * 10)
            change_percent = (i % 3 - 1) * 2.5  # Alternating positive/negative changes
            price_change = base_price * (change_percent / 100)
            
            cached_data.append({
                'symbol': symbol,
                'company_name': f'Mock Company {symbol}',
                'current_price': round(base_price + price_change, 2),
                'previous_price': round(base_price, 2),
                'price_change': round(price_change, 2),
                'percent_change': round(change_percent, 2),
                'current_volume': 1000000 + (i * 100000),
                'average_volume': 1000000,
                'volume_ratio': 1.0 + (i * 0.1),
                'market_cap': 1000000000 + (i * 100000000),
                'rsi': 50.0 + (i * 5),
                'macd_signal': None,
                'technical_signals': [],
                'timestamp': datetime.now().isoformat()
            })
        
        return cached_data
    
    def collect_data(self, symbols: List[str] = None, production_mode: bool = True) -> Dict:
        """Collect data from multiple sources with fallback and rate limiting"""
        logger.info("Starting unified data collection with fallback and rate limiting")
        
        # Use provided symbols or get from FMP
        if symbols is None:
            symbols = fmp_stock_collector.symbols[:self.settings.max_symbols_per_collection]
        
        # Ensure symbols is a list
        if not isinstance(symbols, list):
            symbols = []
        
        logger.info(f"Collecting data for {len(symbols)} symbols")
        
        # Track critical errors
        critical_errors = []
        
        # Try each source in order
        for source_name, source_func in self.sources:
            success, data, message = source_func(symbols)
            
            # Check for critical API errors
            if not success and any(error_code in message for error_code in ['429', '401', '403', '500', '502', '503']):
                critical_errors.append(f"{source_name}: {message}")
                logger.error(f"Critical API error from {source_name}: {message}")
                
                # If we have critical errors from multiple sources, pause collection
                if len(critical_errors) >= 2:
                    logger.error("Multiple critical API errors detected. Pausing data collection.")
                    return {
                        'collection_success': False,
                        'error': f'Critical API errors detected: {", ".join(critical_errors)}. Please check API keys and rate limits.',
                        'data_source': 'Failed - API Errors',
                        'critical_errors': critical_errors,
                        'timestamp': datetime.now().isoformat()
                    }
                continue
            
            if success and data:
                # Check if we have sufficient data for meaningful analysis
                if len(data) < 5:
                    logger.warning(f"Insufficient data from {source_name}: only {len(data)} stocks collected")
                    continue
                
                # Sort by percent change
                data.sort(key=lambda x: x.get('percent_change', 0), reverse=True)
                
                # Get top winners and losers
                winners = [stock for stock in data if stock.get('percent_change', 0) > 0][:5]
                losers = [stock for stock in data if stock.get('percent_change', 0) < 0][:5]
                
                # Ensure we have enough data for analysis
                if len(winners) < 3 or len(losers) < 1:
                    logger.warning(f"Insufficient winners/losers from {source_name}: {len(winners)} winners, {len(losers)} losers")
                    continue
                
                # Create market summary
                market_summary = {
                    'total_stocks_analyzed': len(data),
                    'total_nasdaq_100_stocks': 100,  # NASDAQ-100 has 100 stocks
                    'advancing_stocks': len([s for s in data if s.get('percent_change', 0) > 0]),
                    'declining_stocks': len([s for s in data if s.get('percent_change', 0) < 0]),
                    'average_change': sum(s.get('percent_change', 0) for s in data) / len(data),
                    'market_sentiment': 'Mixed',  # Default sentiment
                    'market_date': datetime.now().isoformat(),
                    'collection_timestamp': datetime.now().isoformat(),
                    'data_source': source_name,
                    'market_coverage': f"Analyzing {len(data)} representative NASDAQ-100 stocks"
                }
                
                # Try to get market sentiment if available
                if source_name == "FMP":
                    try:
                        sentiment = fmp_stock_collector.analyze_market_sentiment(data)
                        market_summary['market_sentiment'] = sentiment.get('market_sentiment', 'Mixed')
                    except:
                        pass
                
                # Get economic calendar data
                try:
                    economic_data = economic_calendar.get_comprehensive_calendar()
                    market_summary['economic_calendar'] = economic_data
                except Exception as e:
                    logger.warning(f"Failed to get economic calendar data: {str(e)}")
                    market_summary['economic_calendar'] = None
                
                # Get enhanced news analysis
                try:
                    enhanced_news = news_collector.get_enhanced_market_news(
                        symbols=[stock['symbol'] for stock in data], 
                        stock_data=data
                    )
                    market_summary['enhanced_news'] = enhanced_news
                except Exception as e:
                    logger.warning(f"Failed to get enhanced news analysis: {str(e)}")
                    market_summary['enhanced_news'] = None
                
                # Get free news analysis as backup/enhancement
                try:
                    free_news = free_news_collector.get_comprehensive_free_news("NASDAQ stock market", 10)
                    if free_news:
                        market_summary['free_news'] = {
                            'articles': free_news,
                            'article_count': len(free_news),
                            'sources': list(set(article.get('source', '') for article in free_news)),
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        market_summary['free_news'] = None
                except Exception as e:
                    logger.warning(f"Failed to get free news: {str(e)}")
                    market_summary['free_news'] = None
                
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
            error_message = 'All data sources failed - cannot generate production content without real data'
            if critical_errors:
                error_message += f'. Critical errors: {", ".join(critical_errors)}'
            
            return {
                'collection_success': False,
                'error': error_message,
                'data_source': 'Failed',
                'critical_errors': critical_errors,
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
                'total_stocks_analyzed': len(cached_data),
                'total_nasdaq_100_stocks': 100,  # NASDAQ-100 has 100 stocks
                'advancing_stocks': len([s for s in cached_data if s.get('percent_change', 0) > 0]),
                'declining_stocks': len([s for s in cached_data if s.get('percent_change', 0) < 0]),
                'average_change': sum(s.get('percent_change', 0) for s in cached_data) / len(cached_data),
                'market_sentiment': 'Test Data',
                'market_date': datetime.now().isoformat(),
                'collection_timestamp': datetime.now().isoformat(),
                'data_source': 'Cached/Test Data',
                'market_coverage': f"Analyzing {len(cached_data)} representative NASDAQ-100 stocks"
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