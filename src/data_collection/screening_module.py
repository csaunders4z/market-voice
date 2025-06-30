"""
Screening Module for Market Voices
Phase 1: Collect basic price/volume data for all symbols to identify top movers
"""
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from loguru import logger
import yfinance as yf

from ..config.settings import get_settings
from ..utils.rate_limiter import rate_limiter


class ScreeningModule:
    """Screens all NASDAQ-100 and S&P 500 symbols to identify top movers"""
    
    def __init__(self):
        self.settings = get_settings()
        self.symbols = []
        self._load_symbols()
    
    def _load_symbols(self):
        """Load all NASDAQ-100 and S&P 500 symbols"""
        try:
            from .symbol_loader import symbol_loader
            self.symbols = symbol_loader.get_all_symbols()
            logger.info(f"Screening module loaded {len(self.symbols)} symbols")
        except Exception as e:
            logger.error(f"Failed to load symbols: {str(e)}")
            # Fallback to basic symbols
            self.symbols = [
                "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX",
                "ADBE", "CRM", "PYPL", "INTC", "AMD", "QCOM", "AVGO", "TXN",
                "COST", "PEP", "CSCO", "TMUS", "ORLY", "ADP", "ISRG", "REGN",
                "VRTX", "GILD", "ABNB", "SNPS", "KLAC", "LRCX", "MU", "PANW",
                "CDNS", "MAR", "MELI", "ASML", "CHTR", "WDAY", "FTNT", "PAYX",
                "CTAS", "ROST", "ODFL", "FAST", "BIIB", "ALGN", "DXCM", "IDXX",
                "VRSK", "CPRT", "PCAR", "EXC", "JNJ", "PG", "UNH", "HD", "JPM",
                "BAC", "WMT", "MA", "V", "DIS", "PFE", "ABT", "KO", "TMO", "ACN",
                "MRK", "NKE", "LLY", "DHR", "CVX", "XOM", "VZ", "T", "CMCSA",
                "NEE", "PM", "RTX", "HON", "UPS", "IBM", "LOW", "CAT", "GS",
                "MS", "AXP", "SPGI", "GE", "AMGN", "UNP", "PLD", "SCHW", "DE",
                "LMT", "MDLZ", "ADI", "BRK.B", "WFC", "C", "USB", "PNC", "TFC",
                "COF", "BLK", "CME", "ICE", "MCO", "FIS", "FISV", "GPN", "HUM",
                "ANTM", "CI", "AET", "CVS", "WBA", "MCK", "ABC", "CAH", "HSIC",
                "DVA", "UHS", "HCA", "THC", "LVS", "MGM", "WYNN", "TGT", "TJX",
                "ULTA", "SBUX", "MCD", "YUM", "CMG", "DPZ", "DRI", "HLT", "FOX",
                "NWSA", "PARA", "WBD", "TTD", "MGNI", "FDX", "BA", "NOC", "GD",
                "LHX", "TDG", "TXT", "EMR", "ETN", "ROK", "DOV", "XYL", "AME",
                "FTV", "ITW", "PH", "MMM", "DOW", "DD", "LIN", "APD", "FCX",
                "NEM", "GOLD", "NUE", "STLD", "X", "COP", "EOG", "SLB", "HAL",
                "BKR", "PSX", "VLO", "MPC", "OXY", "PXD", "DVN", "HES", "APA",
                "MRO", "FANG", "CTRA", "EQT", "RRC", "CHK", "SWN", "COG", "RIG",
                "DO", "HP", "NOV", "DUK", "SO", "D", "AEP", "SRE", "XEL", "WEC",
                "DTE", "ED", "EIX", "PEG", "AEE", "CMS", "CNP", "EXC", "FE",
                "NI", "NRG", "PCG", "PNW", "PPL"
            ]
    
    def screen_symbols(self, max_symbols: int = None) -> Dict:
        """
        Phase 1: Screen all symbols to identify top movers
        Returns basic price/volume data for all symbols
        """
        logger.info("Starting Phase 1: Symbol Screening")
        
        if max_symbols:
            symbols_to_screen = self.symbols[:max_symbols]
        else:
            symbols_to_screen = self.symbols
        
        logger.info(f"Screening {len(symbols_to_screen)} symbols for top movers")
        
        # Try multiple sources for screening
        screening_sources = [
            self._screen_with_yahoo_finance,
            self._screen_with_alpha_vantage,
            self._screen_with_fmp_basic
        ]
        
        for source_func in screening_sources:
            try:
                result = source_func(symbols_to_screen)
                if result.get('screening_success') and result.get('screened_data'):
                    logger.info(f"Screening successful using {result.get('data_source')}")
                    return result
            except Exception as e:
                logger.warning(f"Screening source {source_func.__name__} failed: {str(e)}")
                continue
        
        # If all sources fail, return error
        logger.error("All screening sources failed")
        return {
            'screening_success': False,
            'error': 'All screening sources failed',
            'timestamp': datetime.now().isoformat()
        }
    
    def _screen_with_yahoo_finance(self, symbols: List[str]) -> Dict:
        """Screen symbols using Yahoo Finance (fastest and most reliable)"""
        logger.info("Screening with Yahoo Finance")
        
        def fetch_basic_data(symbol: str) -> Optional[Dict]:
            try:
                ticker = yf.Ticker(symbol)
                
                # Get current day's data
                hist = ticker.history(period="2d")
                
                if len(hist) < 2:
                    return None
                
                # Calculate basic metrics
                current_price = hist['Close'].iloc[-1]
                previous_price = hist['Close'].iloc[-2]
                price_change = current_price - previous_price
                percent_change = (price_change / previous_price) * 100
                current_volume = hist['Volume'].iloc[-1]
                avg_volume = ticker.info.get('averageVolume', current_volume)
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
                
                # Get company info
                info = ticker.info
                company_name = info.get('longName', symbol)
                market_cap = info.get('marketCap', 0)
                
                return {
                    'symbol': symbol,
                    'company_name': company_name,
                    'current_price': round(current_price, 2),
                    'previous_price': round(previous_price, 2),
                    'price_change': round(price_change, 2),
                    'percent_change': round(percent_change, 2),
                    'current_volume': current_volume,
                    'average_volume': avg_volume,
                    'volume_ratio': round(volume_ratio, 2),
                    'market_cap': market_cap,
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.debug(f"Failed to screen {symbol}: {str(e)}")
                return None
        
        # Process symbols in batches
        screened_data = rate_limiter.batch_process(
            items=symbols,
            batch_size=self.settings.yahoo_batch_size,
            batch_delay=self.settings.yahoo_batch_delay,
            process_func=fetch_basic_data,
            api_name="Yahoo Finance Screening"
        )
        
        if screened_data:
            # Sort by percent change
            screened_data.sort(key=lambda x: x.get('percent_change', 0), reverse=True)
            
            # Identify top movers
            winners = [stock for stock in screened_data if stock.get('percent_change', 0) > 0][:5]
            losers = [stock for stock in screened_data if stock.get('percent_change', 0) < 0][:5]
            
            return {
                'screening_success': True,
                'data_source': 'Yahoo Finance',
                'screened_data': screened_data,
                'winners': winners,
                'losers': losers,
                'total_screened': len(screened_data),
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'screening_success': False,
                'error': 'No data collected from Yahoo Finance',
                'data_source': 'Yahoo Finance',
                'timestamp': datetime.now().isoformat()
            }
    
    def _screen_with_alpha_vantage(self, symbols: List[str]) -> Dict:
        """Screen symbols using Alpha Vantage"""
        logger.info("Screening with Alpha Vantage")
        
        av_api_key = self.settings.alpha_vantage_api_key
        if not av_api_key or av_api_key == "DUMMY":
            return {
                'screening_success': False,
                'error': 'Alpha Vantage API key not configured',
                'data_source': 'Alpha Vantage',
                'timestamp': datetime.now().isoformat()
            }
        
        def fetch_basic_data(symbol: str) -> Optional[Dict]:
            try:
                base_url = "https://www.alphavantage.co/query"
                
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
                    return None
                
                # Parse basic data
                current_price = float(quote.get('05. price', 0))
                previous_price = float(quote.get('08. previous close', current_price))
                price_change = float(quote.get('09. change', 0))
                percent_change = float(quote.get('10. change percent', '0%').replace('%', ''))
                volume = int(quote.get('06. volume', 0))
                
                return {
                    'symbol': symbol,
                    'company_name': symbol,  # Alpha Vantage doesn't provide company name in quote
                    'current_price': round(current_price, 2),
                    'previous_price': round(previous_price, 2),
                    'price_change': round(price_change, 2),
                    'percent_change': round(percent_change, 2),
                    'current_volume': volume,
                    'average_volume': volume,  # Alpha Vantage doesn't provide avg volume in quote
                    'volume_ratio': 1.0,  # Default since we don't have avg volume
                    'market_cap': 0,  # Not available in quote endpoint
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.debug(f"Failed to screen {symbol} with Alpha Vantage: {str(e)}")
                return None
        
        # Process symbols in batches
        screened_data = rate_limiter.batch_process(
            items=symbols,
            batch_size=self.settings.alpha_vantage_batch_size,
            batch_delay=self.settings.alpha_vantage_batch_delay,
            process_func=fetch_basic_data,
            api_name="Alpha Vantage Screening"
        )
        
        if screened_data:
            # Sort by percent change
            screened_data.sort(key=lambda x: x.get('percent_change', 0), reverse=True)
            
            # Identify top movers
            winners = [stock for stock in screened_data if stock.get('percent_change', 0) > 0][:5]
            losers = [stock for stock in screened_data if stock.get('percent_change', 0) < 0][:5]
            
            return {
                'screening_success': True,
                'data_source': 'Alpha Vantage',
                'screened_data': screened_data,
                'winners': winners,
                'losers': losers,
                'total_screened': len(screened_data),
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'screening_success': False,
                'error': 'No data collected from Alpha Vantage',
                'data_source': 'Alpha Vantage',
                'timestamp': datetime.now().isoformat()
            }
    
    def _screen_with_fmp_basic(self, symbols: List[str]) -> Dict:
        """Screen symbols using FMP basic quote endpoint"""
        logger.info("Screening with FMP basic quotes")
        
        fmp_api_key = self.settings.fmp_api_key
        if not fmp_api_key or fmp_api_key == "DUMMY":
            return {
                'screening_success': False,
                'error': 'FMP API key not configured',
                'data_source': 'FMP',
                'timestamp': datetime.now().isoformat()
            }
        
        def fetch_basic_data(symbol: str) -> Optional[Dict]:
            try:
                url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={fmp_api_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if not data or not isinstance(data, list):
                    return None
                
                info = data[0]
                
                # Calculate basic metrics
                current_volume = info.get('volume', 0)
                avg_volume = info.get('avgVolume', current_volume)
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
                
                return {
                    'symbol': info.get('symbol', symbol),
                    'company_name': info.get('name', symbol),
                    'current_price': info.get('price', 0),
                    'previous_price': info.get('previousClose', 0),
                    'price_change': info.get('change', 0),
                    'percent_change': info.get('changesPercentage', 0),
                    'current_volume': current_volume,
                    'average_volume': avg_volume,
                    'volume_ratio': volume_ratio,
                    'market_cap': info.get('marketCap', 0),
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.debug(f"Failed to screen {symbol} with FMP: {str(e)}")
                return None
        
        # Process symbols in batches
        screened_data = rate_limiter.batch_process(
            items=symbols,
            batch_size=self.settings.fmp_batch_size,
            batch_delay=self.settings.fmp_batch_delay,
            process_func=fetch_basic_data,
            api_name="FMP Screening"
        )
        
        if screened_data:
            # Sort by percent change
            screened_data.sort(key=lambda x: x.get('percent_change', 0), reverse=True)
            
            # Identify top movers
            winners = [stock for stock in screened_data if stock.get('percent_change', 0) > 0][:5]
            losers = [stock for stock in screened_data if stock.get('percent_change', 0) < 0][:5]
            
            return {
                'screening_success': True,
                'data_source': 'FMP',
                'screened_data': screened_data,
                'winners': winners,
                'losers': losers,
                'total_screened': len(screened_data),
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'screening_success': False,
                'error': 'No data collected from FMP',
                'data_source': 'FMP',
                'timestamp': datetime.now().isoformat()
            }


# Global instance
screening_module = ScreeningModule() 