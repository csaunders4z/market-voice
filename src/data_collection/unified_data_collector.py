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

from src.config.settings import get_settings
from src.utils.rate_limiter import api_rate_limiter, rate_limiter
from src.data_collection.fmp_stock_data import fmp_stock_collector
from src.data_collection.news_collector import news_collector
from .economic_calendar import economic_calendar
from .free_news_sources import free_news_collector
from .symbol_loader import symbol_loader


class UnifiedDataCollector:
    """Unified data collector with multiple source fallback"""
    
    def __init__(self):
        self.settings = get_settings()
        from .finnhub_data_collector import finnhub_data_collector
        # Data source priority: Finnhub (batch, cost-effective), then FMP, Yahoo Finance, Alpha Vantage
        self.sources = [
            ("Finnhub", self._collect_finnhub_data),
            ("FMP", self._collect_fmp_data),
            ("Yahoo Finance", self._collect_yf_data),
            ("Alpha Vantage", self._collect_av_data)
        ]
        self._finnhub_consecutive_failures = 0
        self._finnhub_failure_threshold = 5  # configurable
        self._finnhub_disabled_for_session = False
        # Global circuit breaker/session disable for Alpha Vantage
        self._av_consecutive_failures = 0
        self._av_failure_threshold = 5  # configurable
        self._av_disabled_for_session = False
        # Global circuit breaker/session disable for FMP
        self._fmp_consecutive_failures = 0
        self._fmp_failure_threshold = 5  # configurable
        self._fmp_disabled_for_session = False
        
    def _collect_fmp_data(self, symbols: List[str]) -> Tuple[bool, List[Dict], str]:
        """Collect data from FMP API with rate limiting and global circuit breaker"""
        if self._fmp_disabled_for_session:
            logger.error(f"FMP API disabled for this session after {self._fmp_failure_threshold} consecutive failures. Skipping all FMP requests.")
            return False, [], f"FMP disabled for session after {self._fmp_failure_threshold} consecutive failures"
        try:
            logger.info("Attempting to collect data from FMP API...")
            
            # Use FMP collector with provided symbols
            original_symbols = fmp_stock_collector.symbols
            fmp_stock_collector.symbols = symbols
            
            stock_data = fmp_stock_collector.collect_data()
            
            if stock_data:
                self._fmp_consecutive_failures = 0  # Reset on success
                # Analyze market sentiment
                market_sentiment = fmp_stock_collector.analyze_market_sentiment(stock_data)
                
                # Get news data
                news_data = news_collector.get_market_news(
                    symbols=[stock['symbol'] for stock in stock_data], 
                    stock_data=stock_data
                )
                
                # ENHANCED: Attach news articles directly to stock data for easier script generation access
                for stock in stock_data:
                    symbol = stock['symbol']
                    
                    # Attach news summary (existing functionality)
                    if symbol in news_data.get('news_summaries', {}):
                        stock['news_summary'] = news_data['news_summaries'][symbol]
                    
                    # ENHANCED: Attach full news articles (today's articles only)
                    if symbol in news_data.get('company_news', {}):
                        # Filter to today's articles only
                        today_articles = [article for article in news_data['company_news'][symbol] 
                                        if article.get('published_at') and 
                                        datetime.fromisoformat(article['published_at'].replace('Z', '+00:00')).date() == datetime.now().date()]
                        stock['news_articles'] = today_articles[:5]  # Top 5 today's articles
                    else:
                        stock['news_articles'] = []
                    
                    # Attach comprehensive news if available
                    if symbol in news_data.get('comprehensive_news', {}):
                        comp_news = news_data['comprehensive_news'][symbol]
                        stock['news_analysis'] = comp_news.get('summary', '')
                        stock['news_sources'] = comp_news.get('sources', [])
                    else:
                        stock['news_analysis'] = ''
                        stock['news_sources'] = []
                
                logger.info(f"FMP collection successful: {len(stock_data)} stocks")
                return True, stock_data, "FMP API"
            else:
                self._fmp_consecutive_failures += 1
                if self._fmp_consecutive_failures >= self._fmp_failure_threshold:
                    self._fmp_disabled_for_session = True
                    logger.error(f"FMP API disabled for the remainder of this session after {self._fmp_failure_threshold} consecutive failures.")
                logger.warning("FMP collection returned no data")
                return False, [], "FMP API - No data"
                
        except Exception as e:
            self._fmp_consecutive_failures += 1
            if self._fmp_consecutive_failures >= self._fmp_failure_threshold:
                self._fmp_disabled_for_session = True
                logger.error(f"FMP API disabled for the remainder of this session after {self._fmp_failure_threshold} consecutive failures (exception path).")
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
        """Collect data from Alpha Vantage with rate limiting and global circuit breaker"""
        if self._av_disabled_for_session:
            logger.error(f"Alpha Vantage API disabled for this session after {self._av_failure_threshold} consecutive failures. Skipping all AV requests.")
            return False, [], f"Alpha Vantage disabled for session after {self._av_failure_threshold} consecutive failures"
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
                    # On each symbol failure, increment consecutive failure counter
                    self._av_consecutive_failures += 1
                    if self._av_consecutive_failures >= self._av_failure_threshold:
                        self._av_disabled_for_session = True
                        logger.error(f"Alpha Vantage API disabled for the remainder of this session after {self._av_failure_threshold} consecutive failures.")
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
                self._av_consecutive_failures = 0  # reset on success
                return True, all_data, "Alpha Vantage"
            else:
                logger.warning("Alpha Vantage collection returned no data")
                # Increment consecutive failure counter for batch failure
                self._av_consecutive_failures += 1
                if self._av_consecutive_failures >= self._av_failure_threshold:
                    self._av_disabled_for_session = True
                    logger.error(f"Alpha Vantage API disabled for the remainder of this session after {self._av_failure_threshold} consecutive failures.")
                return False, [], "Alpha Vantage - No data"
                
        except Exception as e:
            logger.error(f"Alpha Vantage collection failed: {str(e)}")
            self._av_consecutive_failures += 1
            if self._av_consecutive_failures >= self._av_failure_threshold:
                self._av_disabled_for_session = True
                logger.error(f"Alpha Vantage API disabled for the remainder of this session after {self._av_failure_threshold} consecutive failures (exception path).")
            return False, [], f"Alpha Vantage - {str(e)}"
    
    def _create_cached_data(self, symbols: List[str]) -> List[Dict]:
        """Create cached/mock data for testing"""
        cached_data = []
        for i, symbol in enumerate(symbols):
            # Create realistic mock data
            base_price = 100 + (i * 10)
            change_percent = (i % 3 - 1) * 2.5  # Alternating positive/negative changes
            price_change = base_price * (change_percent / 100)
            
            # Create mock news data for testing
            mock_news_articles = [
                {
                    'title': f'Mock News: {symbol} Shows Strong Performance',
                    'source': 'Mock News Source',
                    'published_at': datetime.now().isoformat(),
                    'description': f'Mock news article about {symbol} performance'
                }
            ]
            
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
                'timestamp': datetime.now().isoformat(),
                # ENHANCED: Include news fields for testing
                'news_articles': mock_news_articles,
                'news_analysis': f'Mock analysis: {symbol} moved due to mock market conditions',
                'news_sources': ['Mock News Source']
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
        
        # Initialize market_summary and sentiment dicts
        market_summary = {}
        sentiment = {}
        
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
                try:
                    market_summary['market_sentiment'] = sentiment.get('market_sentiment', 'Mixed')
                except Exception:
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
                    
                    # ENHANCED: Attach news articles directly to each stock for easier script generation access
                    if enhanced_news and enhanced_news.get('collection_success'):
                        company_analysis = enhanced_news.get('company_analysis', {})
                        
                        # Attach news articles to each stock in winners and losers (recent articles only)
                        stocks_with_news = 0
                        total_articles_attached = 0
                        
                        for stock in winners + losers:
                            symbol = stock.get('symbol', '')
                            if symbol in company_analysis:
                                # Filter to recent articles (last 24 hours in market timezone)
                                all_articles = company_analysis[symbol].get('articles', [])
                                recent_articles = self._filter_recent_articles(all_articles)
                                
                                if recent_articles:
                                    stock['news_articles'] = recent_articles[:5]  # Top 5 recent articles
                                    stock['news_analysis'] = company_analysis[symbol].get('analysis_text', '')
                                    stock['news_sources'] = company_analysis[symbol].get('sources', [])
                                    stocks_with_news += 1
                                    total_articles_attached += len(recent_articles)
                                    logger.debug(f"  {symbol}: {len(recent_articles)} articles attached")
                                else:
                                    # Initialize empty arrays to avoid None values
                                    stock['news_articles'] = []
                                    stock['news_analysis'] = ''
                                    stock['news_sources'] = []
                                    logger.debug(f"  {symbol}: No recent articles found")
                            else:
                                # Fallback: try to get basic news data
                                try:
                                    basic_news = news_collector.get_market_news(symbols=[symbol])
                                    if symbol in basic_news.get('company_news', {}):
                                        # Filter to recent articles only
                                        all_articles = basic_news['company_news'][symbol]
                                        recent_articles = self._filter_recent_articles(all_articles)
                                        if recent_articles:
                                            stock['news_articles'] = recent_articles[:3]  # Top 3 recent articles
                                            stocks_with_news += 1
                                            total_articles_attached += len(recent_articles)
                                        else:
                                            stock['news_articles'] = []
                                    else:
                                        stock['news_articles'] = []
                                except Exception as e:
                                    logger.debug(f"Fallback news collection failed for {symbol}: {e}")
                                    stock['news_articles'] = []
                                
                                stock['news_analysis'] = ''
                                stock['news_sources'] = []
                        
                        logger.info(f"News attachment complete: {stocks_with_news}/{len(winners + losers)} stocks have news, {total_articles_attached} total articles")
                    
                except Exception as e:
                    logger.warning(f"Failed to get enhanced news analysis: {str(e)}")
                    market_summary['enhanced_news'] = None
                    
                    # Fallback: try to get basic news data for top movers
                    try:
                        basic_news = news_collector.get_market_news(
                            symbols=[stock['symbol'] for stock in winners + losers]
                        )
                        
                        for stock in winners + losers:
                            symbol = stock.get('symbol', '')
                            if symbol in basic_news.get('company_news', {}):
                                stock['news_articles'] = basic_news['company_news'][symbol][:3]  # Top 3 articles
                            else:
                                stock['news_articles'] = []
                            stock['news_analysis'] = ''
                            stock['news_sources'] = []
                        
                        logger.info(f"Attached basic news articles to {len(winners + losers)} top movers (fallback)")
                    except Exception as fallback_error:
                        logger.warning(f"Failed to get basic news data: {str(fallback_error)}")
                        # Ensure all stocks have empty news arrays
                        for stock in winners + losers:
                            stock['news_articles'] = []
                            stock['news_analysis'] = ''
                            stock['news_sources'] = []
                
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
            
            nasdaq100_count = len(symbol_loader.get_nasdaq_100_symbols())
            sp500_count = len(symbol_loader.get_sp_500_symbols())
            market_summary = {
                'total_stocks_analyzed': len(cached_data),
                'total_nasdaq_100_stocks': nasdaq100_count,
                'total_sp_500_stocks': sp500_count,
                'total_target_symbols': len(symbols),
                'advancing_stocks': len([s for s in cached_data if s.get('percent_change', 0) > 0]),
                'declining_stocks': len([s for s in cached_data if s.get('percent_change', 0) < 0]),
                'average_change': sum(s.get('percent_change', 0) for s in cached_data) / len(cached_data),
                'market_sentiment': 'Test Data',
                'market_date': datetime.now().isoformat(),
                'collection_timestamp': datetime.now().isoformat(),
                'data_source': 'Cached/Test Data',
                'market_coverage': f"Analyzing {len(cached_data)} representative NASDAQ-100 and S&P 500 stocks"
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


    def _collect_finnhub_data(self, symbols: List[str]) -> Tuple[bool, List[Dict], str]:
        """Collect data from Finnhub with global circuit breaker/session disable logic"""
        if self._finnhub_disabled_for_session:
            logger.error(f"Finnhub API disabled for this session after {self._finnhub_failure_threshold} consecutive failures. Skipping all Finnhub requests.")
            return False, [], "Finnhub - Disabled"

        # Import FinnhubDataCollector instance
        try:
            from .finnhub_data_collector import finnhub_data_collector
        except Exception as e:
            logger.error(f"Could not import finnhub_data_collector: {str(e)}")
            return False, [], f"Finnhub - Import error: {str(e)}"

        results = []
        errors = []
        for symbol in symbols:
            try:
                quote = finnhub_data_collector.get_quote(symbol)
                profile = finnhub_data_collector.get_company_profile(symbol)
                news = finnhub_data_collector.get_news(symbol)
                if quote is None or profile is None:
                    logger.warning(f"Missing data for {symbol} from Finnhub.")
                    errors.append(symbol)
                    continue
                stock_data = {**quote, **profile}
                stock_data['news_articles'] = news if news else []
                # Calculate percent change if possible
                try:
                    if stock_data.get('current_price') is not None and stock_data.get('previous_close') not in (None, 0):
                        stock_data['percent_change'] = ((stock_data['current_price'] - stock_data['previous_close']) / stock_data['previous_close']) * 100
                    else:
                        stock_data['percent_change'] = 0.0
                except Exception as e:
                    stock_data['percent_change'] = 0.0
                results.append(stock_data)
            except Exception as e:
                logger.error(f"Finnhub collection failed for {symbol}: {str(e)}")
                errors.append(symbol)
                continue

        if not results:
            if errors:
                logger.error(f"Finnhub collection failed for all symbols: {errors}")
                self._finnhub_consecutive_failures += 1
                if self._finnhub_consecutive_failures >= self._finnhub_failure_threshold:
                    self._finnhub_disabled_for_session = True
                    logger.error(f"Finnhub API disabled for the remainder of this session after {self._finnhub_failure_threshold} consecutive failures.")
                return False, [], f"Finnhub - All symbols failed: {errors}"
            else:
                logger.warning("Finnhub returned no data.")
                return False, [], "Finnhub - No data"

        # Reset failure counter on success
        self._finnhub_consecutive_failures = 0
        return True, results, "Finnhub"


    def _filter_recent_articles(self, articles: list) -> list:
        """Filter articles to those published in the last 24 hours in market timezone"""
        if not articles:
            return []
        
        try:
            import pytz
            from datetime import datetime, timedelta
            
            # Get current time in market timezone (Eastern)
            market_tz = pytz.timezone('US/Eastern')
            market_now = datetime.now(market_tz)
            cutoff_time = market_now - timedelta(hours=24)
            
            recent_articles = []
            for article in articles:
                if self._is_recent_article(article.get('published_at', ''), cutoff_time):
                    recent_articles.append(article)
            
            logger.debug(f"Filtered {len(recent_articles)}/{len(articles)} articles as recent")
            return recent_articles
            
        except Exception as e:
            logger.error(f"Error filtering recent articles: {e}")
            # Fallback to returning all articles
            return articles
    
    def _is_recent_article(self, published_at: str, cutoff_time) -> bool:
        """Check if article was published after the cutoff time"""
        if not published_at:
            return False
        
        try:
            import pytz
            from datetime import datetime
            
            if 'T' in published_at:
                article_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            else:
                article_date = datetime.fromisoformat(published_at + 'T00:00:00+00:00')
            
            if article_date.tzinfo is None:
                article_date = article_date.replace(tzinfo=pytz.UTC)
            
            return article_date >= cutoff_time
            
        except Exception as e:
            logger.debug(f"Error parsing article date '{published_at}': {e}")
            return False


# Global instance
unified_collector = UnifiedDataCollector()   