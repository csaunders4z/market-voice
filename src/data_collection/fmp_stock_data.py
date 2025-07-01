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

from ..config.settings import get_settings
from ..utils.rate_limiter import api_rate_limiter, rate_limiter


class FMPStockDataCollector:
    """Collects and analyzes stock market data using FMP API"""
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.fmp_api_key
        self.symbols = []  # Will be populated dynamically
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self._load_nasdaq_100_symbols()

    def _redact_apikey(self, url: str) -> str:
        """Redact the apikey query parameter in a URL for logging"""
        return re.sub(r'(apikey=)[^&]+', r'\1[REDACTED]', url)

    @api_rate_limiter.fmp_request
    def _load_nasdaq_100_symbols(self):
        """Dynamically load the current NASDAQ-100 symbols from FMP API"""
        try:
            url = f"{self.base_url}/nasdaq_constituent?apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and isinstance(data, list):
                self.symbols = [item.get('symbol', '') for item in data if item.get('symbol')]
                logger.info(f"Loaded {len(self.symbols)} NASDAQ-100 symbols from FMP API")
                logger.debug(f"First 10 symbols: {self.symbols[:10]}")
            else:
                logger.warning("Failed to load NASDAQ-100 symbols, using fallback list")
                self._use_fallback_symbols()
                
        except Exception as e:
            redacted_url = self._redact_apikey(url)
            logger.error(f"Error loading NASDAQ-100 symbols: {str(e)} | URL: {redacted_url}")
            logger.info("Using fallback symbol list")
            self._use_fallback_symbols()

    def _use_fallback_symbols(self):
        """Use a comprehensive fallback list of current S&P 500 and NASDAQ-100 stocks"""
        self.symbols = [
            "MSFT",
            "TSN",
            "COO",
            "SWKS",
            "HII",
            "MKC",
            "EXPD",
            "TMUS",
            "XOM",
            "GOOGL",
            "PLD",
            "AON",
            "VRTX",
            "AWK",
            "TFC",
            "CBRE",
            "INTC",
            "LIN",
            "IDXX",
            "NRG",
            "IBM",
            "BA",
            "EXR",
            "YUM",
            "TROW",
            "PEG",
            "ISRG",
            "SJM",
            "MO",
            "AMT",
            "CCI",
            "TEL",
            "BR",
            "SLB",
            "ECL",
            "UAL",
            "BRK-B",
            "T",
            "CF",
            "REGN",
            "MELI",
            "DHR",
            "IRM",
            "UBER",
            "MDT",
            "KDP",
            "MS",
            "SYK",
            "WDC",
            "DD",
            "CRL",
            "GS",
            "PRU",
            "KMI",
            "PAYX",
            "PCAR",
            "PWR",
            "EMR",
            "J",
            "DGX",
            "TPR",
            "MNST",
            "CCEP",
            "DIS",
            "WEC",
            "IFF",
            "DTE",
            "AJG",
            "ADSK",
            "AZN",
            "EXE",
            "EIX",
            "MET",
            "DXCM",
            "CTAS",
            "DOV",
            "ELV",
            "MCHP",
            "REG",
            "MSTR",
            "MRNA",
            "GM",
            "CPAY",
            "SW",
            "DVN",
            "NKE",
            "DVA",
            "APD",
            "HIG",
            "HON",
            "UHS",
            "MCK",
            "QCOM",
            "MCD",
            "NVR",
            "AEP",
            "INCY",
            "BKNG",
            "COIN",
            "PAYC",
            "V",
            "FITB",
            "TXT",
            "NWSA",
            "SWK",
            "DELL",
            "EXPE",
            "MPC",
            "NDSN",
            "PSA",
            "MMC",
            "SYF",
            "VTRS",
            "FDS",
            "CNC",
            "MTB",
            "KEYS",
            "DOC",
            "JNJ",
            "SNPS",
            "COF",
            "WAT",
            "APP",
            "NCLH",
            "DASH",
            "SMCI",
            "OXY",
            "ACN",
            "NTRS",
            "K",
            "C",
            "BX",
            "EXC",
            "SO",
            "MMM",
            "WYNN",
            "DG",
            "UDR",
            "FOX",
            "LII",
            "PG",
            "DUK",
            "IR",
            "IEX",
            "BXP",
            "RTX",
            "CMS",
            "IQV",
            "PEP",
            "STX",
            "GPC",
            "VST",
            "VLO",
            "MLM",
            "LW",
            "CEG",
            "FCX",
            "CME",
            "MU",
            "PTC",
            "BG",
            "AVY",
            "ULTA",
            "BSX",
            "VLTO",
            "HUBB",
            "ALL",
            "GD",
            "GEV",
            "CPB",
            "STE",
            "TRGP",
            "CARR",
            "CSCO",
            "CSGP",
            "HOLX",
            "TTWO",
            "RL",
            "OKE",
            "AEE",
            "LNT",
            "CSX",
            "GRMN",
            "LUV",
            "LEN",
            "TER",
            "KMX",
            "SPG",
            "WAB",
            "GE",
            "LH",
            "AXON",
            "ASML",
            "GOOG",
            "APH",
            "CTVA",
            "DLR",
            "GWW",
            "DE",
            "MSCI",
            "TDG",
            "FANG",
            "MPWR",
            "CAG",
            "EG",
            "BALL",
            "LYV",
            "CPRT",
            "EQT",
            "CZR",
            "EQIX",
            "STT",
            "MDLZ",
            "CVX",
            "META",
            "CMCSA",
            "WST",
            "DECK",
            "ROST",
            "BKR",
            "RCL",
            "FE",
            "AME",
            "SHW",
            "LOW",
            "ED",
            "ITW",
            "WBD",
            "FDX",
            "O",
            "APA",
            "ERIE",
            "PFE",
            "ROP",
            "GDDY",
            "ABBV",
            "FRT",
            "FIS",
            "TMO",
            "VICI",
            "XYL",
            "ZBH",
            "AXP",
            "TDY",
            "MHK",
            "TT",
            "MRK",
            "HPE",
            "WBA",
            "PDD",
            "CINF",
            "TRMB",
            "MAR",
            "ES",
            "GPN",
            "BLK",
            "AMGN",
            "EA",
            "BLDR",
            "CAH",
            "EBAY",
            "WDAY",
            "JPM",
            "PPG",
            "WMT",
            "EMN",
            "HRL",
            "DOW",
            "TSLA",
            "WMB",
            "NXPI",
            "LYB",
            "ARE",
            "SBUX",
            "WRB",
            "URI",
            "BMY",
            "LHX",
            "UNP",
            "CBOE",
            "PM",
            "WSM",
            "EQR",
            "D",
            "PKG",
            "HPQ",
            "MA",
            "KO",
            "WTW",
            "ENPH",
            "BIIB",
            "AIG",
            "UPS",
            "CHD",
            "VZ",
            "KKR",
            "ABT",
            "FOXA",
            "SPGI",
            "ETN",
            "CAT",
            "HUM",
            "MGM",
            "ESS",
            "EVRG",
            "STLD",
            "AES",
            "COST",
            "AMP",
            "WM",
            "AAPL",
            "SHOP",
            "ON",
            "TPL",
            "LKQ",
            "ODFL",
            "INVH",
            "HAS",
            "LDOS",
            "TTD",
            "MRVL",
            "LULU",
            "CHRW",
            "EOG",
            "FTNT",
            "PODD",
            "CTRA",
            "CLX",
            "XEL",
            "FICO",
            "JBL",
            "ADP",
            "BAC",
            "SNA",
            "VMC",
            "GL",
            "PGR",
            "EL",
            "ORCL",
            "JKHY",
            "ICE",
            "COR",
            "CNP",
            "USB",
            "PNC",
            "AMZN",
            "FSLR",
            "WY",
            "VRSN",
            "EFX",
            "ALGN",
            "JBHT",
            "APTV",
            "FI",
            "VTR",
            "PPL",
            "TXN",
            "TECH",
            "NTAP",
            "ZBRA",
            "ADBE",
            "KLAC",
            "KHC",
            "CMG",
            "MCO",
            "VRSK",
            "GNRC",
            "HWM",
            "ATO",
            "KMB",
            "ALB",
            "MTD",
            "JCI",
            "KEY",
            "KIM",
            "BEN",
            "KR",
            "EW",
            "AVGO",
            "CPT",
            "TRV",
            "INTU",
            "HD",
            "CCL",
            "PH",
            "NWS",
            "ARM",
            "JNPR",
            "HCA",
            "NOC",
            "GILD",
            "CRWD",
            "RMD",
            "AMCR",
            "APO",
            "NVDA",
            "RF",
            "CMI",
            "BAX",
            "PANW",
            "STZ",
            "KVUE",
            "ABNB",
            "DDOG",
            "SCHW",
            "A",
            "ZTS",
            "TYL",
            "PHM",
            "PARA",
            "COP",
            "PNR",
            "AZO",
            "PSX",
            "POOL",
            "LLY",
            "ACGL",
            "NUE",
            "HAL",
            "AMAT",
            "MKTX",
            "ADI",
            "CVS",
            "BRO",
            "L",
            "HST",
            "TEAM",
            "GLW",
            "ROL",
            "GEHC",
            "RVTY",
            "NOW",
            "MOH",
            "SYY",
            "HBAN",
            "ROK",
            "RSG",
            "TAP",
            "ADM",
            "ALLE",
            "CRM",
            "OMC",
            "UNH",
            "MAA",
            "DLTR",
            "EPAM",
            "DPZ",
            "AOS",
            "PCG",
            "MSI",
            "FTV",
            "HLT",
            "ZS",
            "RJF",
            "NI",
            "FAST",
            "PFG",
            "CHTR",
            "CTSH",
            "IP",
            "MAS",
            "DHI",
            "SOLV",
            "PYPL",
            "BK",
            "DRI",
            "NSC",
            "TSCO",
            "AMD",
            "MTCH",
            "NDAQ",
            "TKO",
            "NEE",
            "ORLY",
            "OTIS",
            "CI",
            "LVS",
            "TGT",
            "IPG",
            "NEM",
            "BBY",
            "BDX",
            "MOS",
            "FFIV",
            "ANSS",
            "TJX",
            "DAL",
            "CDW",
            "CFG",
            "F",
            "GIS",
            "HES",
            "DAY",
            "PNW",
            "IT",
            "BF.B",
            "CDNS",
            "SRE",
            "ETR",
            "SBAC",
            "IVZ",
            "AIZ",
            "GEN",
            "LMT",
            "WELL",
            "CB",
            "AKAM",
            "AFL",
            "AVB",
            "HSY",
            "CL",
            "LRCX",
            "PLTR",
            "GFS",
            "HSIC",
            "NFLX",
            "WFC",
            "ANET"
        ]
        logger.info(f"Using comprehensive fallback list with {len(self.symbols)} unique S&P 500 and NASDAQ-100 symbols")

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
            
            # Fetch additional data for significant movers or high volume
            earnings_data = None
            analyst_data = None
            insider_data = None
            
            if abs(info.get('changesPercentage', 0)) > 3 or volume_ratio > 1.5:
                # Only fetch additional data for significant movers to avoid API limits
                try:
                    earnings_data = self.fetch_earnings_calendar(symbol)
                    analyst_data = self.fetch_analyst_ratings(symbol)
                    insider_data = self.fetch_insider_trading(symbol)
                except Exception as e:
                    logger.warning(f"Failed to fetch additional data for {symbol}: {str(e)}")
            
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
                'earnings_data': earnings_data,
                'analyst_data': analyst_data,
                'insider_data': insider_data,
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

    @api_rate_limiter.fmp_request
    def fetch_earnings_calendar(self, symbol: str) -> Optional[Dict]:
        """Fetch upcoming earnings data for a symbol"""
        try:
            url = f"{self.base_url}/earnings-calendar/{symbol}?apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                return None
            
            # Get the next earnings date
            upcoming_earnings = None
            for earnings in data:
                if earnings.get('date') and earnings.get('date') >= datetime.now().strftime('%Y-%m-%d'):
                    upcoming_earnings = {
                        'date': earnings.get('date'),
                        'time': earnings.get('time'),
                        'estimate': earnings.get('epsEstimate'),
                        'actual': earnings.get('epsActual'),
                        'revenue_estimate': earnings.get('revenueEstimate'),
                        'revenue_actual': earnings.get('revenueActual')
                    }
                    break
            
            return upcoming_earnings
            
        except Exception as e:
            logger.error(f"Error fetching earnings calendar for {symbol}: {str(e)}")
            return None

    @api_rate_limiter.fmp_request
    def fetch_analyst_ratings(self, symbol: str) -> Optional[Dict]:
        """Fetch analyst ratings and price targets"""
        try:
            url = f"{self.base_url}/analyst-stock-recommendations/{symbol}?apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                return None
            
            # Get the most recent ratings
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
            
            avg_price_target = sum(price_targets) / len(price_targets) if price_targets else None
            
            return {
                'consensus': consensus,
                'ratings_count': ratings_count,
                'average_price_target': avg_price_target,
                'recent_ratings': recent_ratings[:3]  # Last 3 for summary
            }
            
        except Exception as e:
            logger.error(f"Error fetching analyst ratings for {symbol}: {str(e)}")
            return None

    @api_rate_limiter.fmp_request
    def fetch_insider_trading(self, symbol: str) -> Optional[Dict]:
        """Fetch recent insider trading activity"""
        try:
            url = f"{self.base_url}/insider-trading/{symbol}?apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                return None
            
            # Get recent insider activity (last 30 days)
            recent_activity = []
            total_buy_value = 0
            total_sell_value = 0
            
            for trade in data[:10]:  # Last 10 trades
                trade_date = trade.get('filingDate')
                if trade_date:
                    # Check if within last 30 days
                    try:
                        trade_datetime = datetime.strptime(trade_date, '%Y-%m-%d')
                        if (datetime.now() - trade_datetime).days <= 30:
                            recent_activity.append(trade)
                            
                            # Calculate values
                            shares = trade.get('securitiesTransacted', 0)
                            price = trade.get('priceAcquired', 0)
                            value = shares * price
                            
                            if trade.get('transactionType', '').lower() == 'buy':
                                total_buy_value += value
                            else:
                                total_sell_value += value
                    except:
                        continue
            
            if recent_activity:
                return {
                    'recent_trades': recent_activity[:5],  # Top 5 recent
                    'total_buy_value': total_buy_value,
                    'total_sell_value': total_sell_value,
                    'net_activity': 'buy' if total_buy_value > total_sell_value else 'sell',
                    'activity_level': 'high' if len(recent_activity) >= 5 else 'moderate' if len(recent_activity) >= 2 else 'low'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching insider trading for {symbol}: {str(e)}")
            return None

# Global instance
fmp_stock_collector = FMPStockDataCollector() 