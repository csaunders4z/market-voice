"""
Deep Analysis Module for Market Voices
Phase 2: Fetch detailed analysis data only for identified top movers
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
import yfinance as yf

from ..config.settings import get_settings
from ..utils.rate_limiter import rate_limiter


class DeepAnalysisModule:
    """Fetches detailed analysis data for identified top movers"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def analyze_top_movers(self, winners: List[Dict], losers: List[Dict]) -> Dict:
        """
        Phase 2: Perform deep analysis on identified top movers
        Returns detailed data for winners and losers
        """
        logger.info("Starting Phase 2: Deep Analysis of Top Movers")
        
        all_movers = winners + losers
        logger.info(f"Performing deep analysis on {len(all_movers)} top movers")
        
        # Analyze each mover with detailed data
        analyzed_movers = []
        
        for mover in all_movers:
            symbol = mover.get('symbol')
            if not symbol:
                continue
                
            logger.info(f"Analyzing {symbol} with deep data")
            detailed_data = self._analyze_single_stock(symbol, mover)
            
            if detailed_data:
                # Merge basic screening data with deep analysis
                merged_data = {**mover, **detailed_data}
                analyzed_movers.append(merged_data)
            else:
                # Keep original data if deep analysis fails
                analyzed_movers.append(mover)
        
        # Separate winners and losers
        analyzed_winners = [mover for mover in analyzed_movers if mover.get('percent_change', 0) > 0][:5]
        analyzed_losers = [mover for mover in analyzed_movers if mover.get('percent_change', 0) < 0][:5]
        
        return {
            'analysis_success': True,
            'analyzed_winners': analyzed_winners,
            'analyzed_losers': analyzed_losers,
            'total_analyzed': len(analyzed_movers),
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_single_stock(self, symbol: str, basic_data: Dict) -> Optional[Dict]:
        """Perform deep analysis on a single stock"""
        try:
            # Try multiple analysis sources
            analysis_sources = [
                self._analyze_with_yahoo_finance,
                self._analyze_with_fmp,
                self._analyze_with_alpha_vantage
            ]
            
            for source_func in analysis_sources:
                try:
                    detailed_data = source_func(symbol, basic_data)
                    if detailed_data:
                        return detailed_data
                except Exception as e:
                    logger.debug(f"Analysis source {source_func.__name__} failed for {symbol}: {str(e)}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Deep analysis failed for {symbol}: {str(e)}")
            return None
    
    def _analyze_with_yahoo_finance(self, symbol: str, basic_data: Dict) -> Optional[Dict]:
        """Analyze stock using Yahoo Finance detailed data"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get earnings calendar
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
            
            # Get price target
            price_target = None
            try:
                info = ticker.info
                price_target = info.get('targetMeanPrice')
            except:
                pass
            
            # Get technical indicators
            technical_data = None
            try:
                hist = ticker.history(period="30d")
                if len(hist) >= 14:
                    # Calculate RSI
                    delta = hist['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    current_rsi = rsi.iloc[-1]
                    
                    # Calculate MACD
                    exp1 = hist['Close'].ewm(span=12).mean()
                    exp2 = hist['Close'].ewm(span=26).mean()
                    macd = exp1 - exp2
                    signal = macd.ewm(span=9).mean()
                    histogram = macd - signal
                    
                    macd_signal = None
                    if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
                        macd_signal = "bullish"
                    elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2]:
                        macd_signal = "bearish"
                    
                    technical_data = {
                        'rsi': round(current_rsi, 2),
                        'macd_signal': macd_signal,
                        'technical_signals': []
                    }
                    
                    # Add technical signals
                    if current_rsi > 70:
                        technical_data['technical_signals'].append("RSI overbought")
                    elif current_rsi < 30:
                        technical_data['technical_signals'].append("RSI oversold")
                    
                    volume_ratio = basic_data.get('volume_ratio', 1.0)
                    if volume_ratio > 2:
                        technical_data['technical_signals'].append("High volume")
                    
                    if macd_signal:
                        technical_data['technical_signals'].append(f"MACD {macd_signal} crossover")
            except Exception as e:
                logger.debug(f"Could not calculate technical indicators for {symbol}: {str(e)}")
            
            return {
                'earnings_data': earnings_data,
                'analyst_data': analyst_data,
                'price_target': price_target,
                'technical_data': technical_data,
                'analysis_source': 'Yahoo Finance'
            }
            
        except Exception as e:
            logger.error(f"Yahoo Finance analysis failed for {symbol}: {str(e)}")
            return None
    
    def _analyze_with_fmp(self, symbol: str, basic_data: Dict) -> Optional[Dict]:
        """Analyze stock using FMP detailed data"""
        try:
            fmp_api_key = self.settings.fmp_api_key
            if not fmp_api_key or fmp_api_key == "DUMMY":
                return None
            
            base_url = "https://financialmodelingprep.com/api/v3"
            
            # Get earnings calendar
            earnings_data = None
            try:
                url = f"{base_url}/earnings-calendar/{symbol}?apikey={fmp_api_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data and isinstance(data, list):
                    # Get the next earnings date
                    for earnings in data:
                        if earnings.get('date') and earnings.get('date') >= datetime.now().strftime('%Y-%m-%d'):
                            earnings_data = {
                                'date': earnings.get('date'),
                                'time': earnings.get('time'),
                                'estimate': earnings.get('epsEstimate'),
                                'actual': earnings.get('epsActual'),
                                'revenue_estimate': earnings.get('revenueEstimate'),
                                'revenue_actual': earnings.get('revenueActual')
                            }
                            break
            except Exception as e:
                logger.debug(f"Could not fetch FMP earnings data for {symbol}: {str(e)}")
            
            # Get analyst ratings
            analyst_data = None
            try:
                url = f"{base_url}/analyst-stock-recommendations/{symbol}?apikey={fmp_api_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data and isinstance(data, list):
                    recent_ratings = data[:5]  # Last 5 ratings
                    
                    # Calculate consensus
                    ratings_count = {'buy': 0, 'hold': 0, 'sell': 0}
                    price_targets = []
                    
                    for rating in recent_ratings:
                        rating_type = rating.get('rating', '').lower()
                        if 'buy' in rating_type:
                            ratings_count['buy'] += 1
                        elif 'hold' in rating_type:
                            ratings_count['hold'] += 1
                        elif 'sell' in rating_type:
                            ratings_count['sell'] += 1
                        
                        price_target = rating.get('priceTarget')
                        if price_target and price_target > 0:
                            price_targets.append(price_target)
                    
                    # Determine consensus
                    total = sum(ratings_count.values())
                    if total > 0:
                        if ratings_count['buy'] > ratings_count['hold'] and ratings_count['buy'] > ratings_count['sell']:
                            consensus = 'buy'
                        elif ratings_count['sell'] > ratings_count['hold'] and ratings_count['sell'] > ratings_count['buy']:
                            consensus = 'sell'
                        else:
                            consensus = 'hold'
                    else:
                        consensus = 'hold'
                    
                    analyst_data = {
                        'consensus': consensus,
                        'ratings_count': ratings_count,
                        'price_targets': price_targets,
                        'average_price_target': sum(price_targets) / len(price_targets) if price_targets else None,
                        'recent_recommendations': recent_ratings[:3]
                    }
            except Exception as e:
                logger.debug(f"Could not fetch FMP analyst data for {symbol}: {str(e)}")
            
            # Get insider trading data
            insider_data = None
            try:
                url = f"{base_url}/insider-trading/{symbol}?apikey={fmp_api_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data and isinstance(data, list):
                    recent_insider = data[:10]  # Last 10 insider transactions
                    
                    # Analyze insider activity
                    buy_volume = sum(t.get('value', 0) for t in recent_insider if t.get('type') == 'buy')
                    sell_volume = sum(t.get('value', 0) for t in recent_insider if t.get('type') == 'sell')
                    
                    activity_level = 'low'
                    if len(recent_insider) > 5:
                        activity_level = 'high'
                    elif len(recent_insider) > 2:
                        activity_level = 'medium'
                    
                    net_activity = 'neutral'
                    if buy_volume > sell_volume * 1.5:
                        net_activity = 'buying'
                    elif sell_volume > buy_volume * 1.5:
                        net_activity = 'selling'
                    
                    insider_data = {
                        'activity_level': activity_level,
                        'net_activity': net_activity,
                        'buy_volume': buy_volume,
                        'sell_volume': sell_volume,
                        'recent_transactions': recent_insider[:5]
                    }
            except Exception as e:
                logger.debug(f"Could not fetch FMP insider data for {symbol}: {str(e)}")
            
            return {
                'earnings_data': earnings_data,
                'analyst_data': analyst_data,
                'insider_data': insider_data,
                'analysis_source': 'FMP'
            }
            
        except Exception as e:
            logger.error(f"FMP analysis failed for {symbol}: {str(e)}")
            return None
    
    def _analyze_with_alpha_vantage(self, symbol: str, basic_data: Dict) -> Optional[Dict]:
        """Analyze stock using Alpha Vantage detailed data"""
        try:
            av_api_key = self.settings.alpha_vantage_api_key
            if not av_api_key or av_api_key == "DUMMY":
                return None
            
            base_url = "https://www.alphavantage.co/query"
            
            # Get company overview
            overview_data = None
            try:
                params = {
                    'function': 'OVERVIEW',
                    'symbol': symbol,
                    'apikey': av_api_key
                }
                
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data and not data.get('Error Message'):
                    overview_data = {
                        'sector': data.get('Sector', ''),
                        'industry': data.get('Industry', ''),
                        'description': data.get('Description', ''),
                        'pe_ratio': data.get('PERatio', ''),
                        'dividend_yield': data.get('DividendYield', ''),
                        'beta': data.get('Beta', '')
                    }
            except Exception as e:
                logger.debug(f"Could not fetch Alpha Vantage overview for {symbol}: {str(e)}")
            
            return {
                'overview_data': overview_data,
                'analysis_source': 'Alpha Vantage'
            }
            
        except Exception as e:
            logger.error(f"Alpha Vantage analysis failed for {symbol}: {str(e)}")
            return None


# Global instance
deep_analysis_module = DeepAnalysisModule() 