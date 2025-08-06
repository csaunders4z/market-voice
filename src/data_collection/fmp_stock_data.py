"""
Stock data collection using Financial Market Prep (FMP) API
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger
import os
import numpy as np
import time
import re
import json
from pathlib import Path

from src.config.settings import get_settings
from ..utils.cache import cached, api_cache
from ..utils.rate_limiter import api_rate_limiter, rate_limiter


class FMPStockDataCollector:
    """Collects and analyzes stock market data using FMP API"""
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.fmp_api_key
        self.symbols = []  # Will be populated dynamically
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self._load_nasdaq_100_symbols()
        
        # Cache directory for persistent storage
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.symbol_cache_file = self.cache_dir / "nasdaq100_symbols.json"

    def _redact_apikey(self, url: str) -> str:
        """Redact the apikey query parameter in a URL for logging"""
        return re.sub(r'(apikey=)[^&]+', r'\1[REDACTED]', url)

    def _load_cached_symbols(self) -> Optional[List[str]]:
        """Load symbols from cache if valid"""
        try:
            if not self.symbol_cache_file.exists():
                return None
                
            # Check if cache is fresh (less than 12 hours old)
            cache_age = time.time() - self.symbol_cache_file.stat().st_mtime
            if cache_age > 12 * 3600:  # 12 hours in seconds
                return None
                
            with open(self.symbol_cache_file, 'r') as f:
                data = json.load(f)
                
            if isinstance(data, list) and all(isinstance(x, str) for x in data):
                logger.info(f"Loaded {len(data)} NASDAQ-100 symbols from cache")
                return data
                
        except Exception as e:
            logger.warning(f"Error loading cached symbols: {str(e)}")
            
        return None
        
    def _save_symbols_to_cache(self, symbols: List[str]):
        """Save symbols to cache"""
        try:
            with open(self.symbol_cache_file, 'w') as f:
                json.dump(symbols, f)
            logger.debug(f"Saved {len(symbols)} symbols to cache")
        except Exception as e:
            logger.warning(f"Failed to save symbols to cache: {str(e)}")

    @api_rate_limiter.fmp_request
    def _load_nasdaq_100_symbols(self):
        """Dynamically load the current NASDAQ-100 symbols from FMP API with caching"""
        # Try to load from cache first
        cached_symbols = self._load_cached_symbols()
        if cached_symbols:
            self.symbols = cached_symbols
            return
            
        # If cache miss or stale, fetch from API
        try:
            url = f"{self.base_url}/nasdaq_constituent?apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and isinstance(data, list):
                symbols = [item.get('symbol', '') for item in data if item.get('symbol')]
                self.symbols = symbols
                logger.info(f"Loaded {len(symbols)} NASDAQ-100 symbols from FMP API")
                logger.debug(f"First 10 symbols: {symbols[:10]}")
                
                # Save to cache for future use
                self._save_symbols_to_cache(symbols)
            else:
                logger.warning("Failed to load NASDAQ-100 symbols, using fallback list")
                self._use_fallback_symbols()
                
        except requests.exceptions.RequestException as e:
            redacted_url = self._redact_apikey(url)
            logger.error(f"Error loading NASDAQ-100 symbols: {str(e)} | URL: {redacted_url}")
            logger.info("Using fallback symbol list")
            self._use_fallback_symbols()
        except Exception as e:
            logger.error(f"Unexpected error loading NASDAQ-100 symbols: {str(e)}")
            self._use_fallback_symbols()

    def _use_fallback_symbols(self):
        """Use a comprehensive fallback list of current S&P 500 and NASDAQ-100 stocks"""
        fallback_symbols = [
            "MSFT", "AAPL", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "NVDA", "BRK-B", "JPM",
            "V", "JNJ", "PG", "UNH", "MA", "HD", "DIS", "BAC", "PFE", "VZ", "CMCSA", "INTC",
            "CSCO", "PEP", "ADBE", "NFLX", "PYPL", "ABT", "TMO", "NKE", "COST", "MRK", "ABBV",
            "TXN", "ACN", "HON", "NEE", "PM", "UNP", "LOW", "ORCL", "LIN", "SBUX", "AMGN",
            "MDT", "T", "CVX", "QCOM", "DHR", "BMY", "TGT", "USB", "CHTR", "GILD", "INTU",
            "AMT", "ISRG", "GS", "LMT", "BKNG", "LRCX", "ADP", "TJX", "DE", "ADI", "MDLZ",
            "REGN", "VRTX", "FISV", "CSX", "ILMN", "MU", "ATVI", "ADSK", "BIIB", "MELI",
            "KLAC", "SNPS", "CDNS", "MCHP", "ASML", "AEP", "DXCM", "CTAS", "WDAY", "EXC",
            "MRNA", "KDP", "KHC", "LULU", "EA", "CRWD", "TEAM", "MTCH", "DOCU", "OKTA",
            "ZM", "PTON", "ROKU", "DDOG", "FTNT", "TTD", "ZS", "NET", "SQ", "SE", "SHOP"
        ]
        
        # Add common index symbols
        fallback_symbols.extend(["SPY", "QQQ", "DIA", "IWM", "VTI", "VOO", "IVV", "VEA", "VWO"])
        
        self.symbols = list(dict.fromkeys(fallback_symbols))  # Remove duplicates while preserving order
        logger.info(f"Using fallback list of {len(self.symbols)} symbols")
        
        # Save to cache to avoid repeated fallback on subsequent runs
        self._save_symbols_to_cache(self.symbols)

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI if insufficient data
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)

    def _calculate_macd(self, prices: List[float]) -> Dict:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < 26:
            return {"macd": 0, "signal": 0, "histogram": 0, "crossover": None}
        
        # Calculate EMAs
        ema12 = np.mean(prices[-12:])  # Simplified EMA calculation
        ema26 = np.mean(prices[-26:])
        
        macd_line = ema12 - ema26
        signal_line = np.mean(prices[-9:])  # Simplified signal line
        
        histogram = macd_line - signal_line
        
        # Determine crossover
        crossover = None
        if len(prices) >= 27:
            prev_ema12 = np.mean(prices[-13:-1])
            prev_ema26 = np.mean(prices[-27:-1])
            prev_macd = prev_ema12 - prev_ema26
            
            if macd_line > signal_line and prev_macd <= signal_line:
                crossover = "bullish"
            elif macd_line < signal_line and prev_macd >= signal_line:
                crossover = "bearish"
        
        return {
            "macd": float(macd_line),
            "signal": float(signal_line),
            "histogram": float(histogram),
            "crossover": crossover
        }

    @api_rate_limiter.fmp_request
    def _fetch_historical_data(self, symbol: str, days: int = 30) -> List[Dict]:
        """Fetch historical price data for technical analysis"""
        try:
            url = f"{self.base_url}/historical-price-full/{symbol}?apikey={self.api_key}"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if not data or 'historical' not in data:
                return []
            
            historical = data['historical'][:days]  # Get last N days
            return historical
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return []

    @api_rate_limiter.fmp_request
    def fetch_stock_data(self, symbol: str) -> Optional[Dict]:
        """Fetch data for a single stock symbol from FMP with technical indicators and additional data"""
        try:
            # Fetch current quote
            url = f"{self.base_url}/quote/{symbol}?apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                logger.warning(f"No data returned for {symbol}")
                return None
            
            info = data[0]
            
            # Calculate volume ratio
            current_volume = info.get('volume', 0)
            avg_volume = info.get('avgVolume', 1)  # Avoid division by zero
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Fetch historical data for technical indicators
            historical_data = self._fetch_historical_data(symbol, 30)
            prices = [float(item['close']) for item in historical_data] if historical_data else []
            
            # Calculate technical indicators
            rsi = self._calculate_rsi(prices) if len(prices) >= 15 else 50.0
            macd_data = self._calculate_macd(prices) if len(prices) >= 26 else {"macd": 0, "signal": 0, "histogram": 0, "crossover": None}
            
            # Determine technical signals
            technical_signals = []
            if rsi > 70:
                technical_signals.append("RSI overbought")
            elif rsi < 30:
                technical_signals.append("RSI oversold")
            
            if volume_ratio > 2:
                technical_signals.append("High volume")
            
            if macd_data.get('crossover'):
                technical_signals.append(f"MACD {macd_data['crossover']} crossover")
            
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
                'rsi': rsi,
                'macd_signal': macd_data.get('crossover'),
                'technical_signals': technical_signals,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            redacted_url = self._redact_apikey(url)
            error_str = str(e)
            if '429' in error_str or 'Too Many Requests' in error_str:
                logger.warning(f"Rate limit hit for {symbol}: {error_str}")
            elif '401' in error_str or '403' in error_str or 'Unauthorized' in error_str:
                logger.error(f"Authorization error for {symbol}: {error_str}")
            elif '500' in error_str or '502' in error_str or '503' in error_str:
                logger.error(f"Server error for {symbol}: {error_str}")
            else:
                logger.error(f"Error fetching FMP data for {symbol}: {error_str} | URL: {redacted_url}")
            return None

    def collect_data(self) -> List[Dict]:
        """Collect data for all symbols with optimized rate limiting and error handling"""
        logger.info("Starting FMP data collection with technical indicators and rate limiting")
        
        # Limit symbols to avoid excessive API calls
        symbols_to_collect = self.symbols[:self.settings.max_symbols_per_collection]
        logger.info(f"Collecting data for {len(symbols_to_collect)} symbols (limited from {len(self.symbols)})")
        
        # Use batch processing with rate limiting and early termination
        all_data = rate_limiter.batch_process(
            items=symbols_to_collect,
            batch_size=self.settings.fmp_batch_size,
            batch_delay=self.settings.fmp_batch_delay,
            process_func=self.fetch_stock_data,
            api_name="FMP",
            max_consecutive_errors=5  # Stop after 5 consecutive errors
        )
        
        logger.info(f"Collected FMP data for {len(all_data)}/{len(symbols_to_collect)} symbols")
        
        # If we have too few successful collections, return empty to trigger fallback
        if len(all_data) < 5:
            logger.warning(f"Insufficient FMP data collected ({len(all_data)} stocks). Triggering fallback.")
            return []
        
        return all_data

    def analyze_market_sentiment(self, stock_data: List[Dict]) -> Dict:
        """Analyze overall market sentiment based on collected data"""
        if not stock_data:
            return {"market_sentiment": "Neutral", "advancing_stocks": 0, "declining_stocks": 0}
        
        advancing = sum(1 for stock in stock_data if stock.get('percent_change', 0) > 0)
        declining = sum(1 for stock in stock_data if stock.get('percent_change', 0) < 0)
        total = len(stock_data)
        
        # Calculate average change
        avg_change = sum(stock.get('percent_change', 0) for stock in stock_data) / total
        
        # Determine sentiment
        if advancing > declining * 1.5 and avg_change > 1:
            sentiment = "Bullish"
        elif declining > advancing * 1.5 and avg_change < -1:
            sentiment = "Bearish"
        else:
            sentiment = "Mixed"
        
        return {
            "market_sentiment": sentiment,
            "advancing_stocks": advancing,
            "declining_stocks": declining,
            "average_change": avg_change,
            "total_stocks": total
        }

# Global instance
fmp_stock_collector = FMPStockDataCollector()