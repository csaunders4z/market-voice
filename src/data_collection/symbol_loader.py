"""
Dynamic symbol list loader for Market Voices
Loads NASDAQ-100 and S&P 500 symbols from reliable public sources
"""
import requests
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from io import StringIO
from loguru import logger
import time
import re

from ..config.settings import get_settings


class SymbolLoader:
    """Dynamically loads NASDAQ-100 and S&P 500 symbol lists"""
    
    def __init__(self):
        self.settings = get_settings()
        self.nasdaq_100_symbols = []
        self.sp_500_symbols = []
        self.last_update = None
        self.update_interval = 3600  # Update every hour
        
    def get_nasdaq_100_symbols(self) -> List[str]:
        """Get NASDAQ-100 symbols with caching"""
        if self._should_update():
            self._load_nasdaq_100_symbols()
        return self.nasdaq_100_symbols.copy()
    
    def get_sp_500_symbols(self) -> List[str]:
        """Get S&P 500 symbols with caching"""
        if self._should_update():
            self._load_sp_500_symbols()
        return self.sp_500_symbols.copy()
    
    def get_all_symbols(self) -> List[str]:
        """Get combined unique symbols from both indices"""
        nasdaq = set(self.get_nasdaq_100_symbols())
        sp500 = set(self.get_sp_500_symbols())
        combined = list(nasdaq.union(sp500))
        logger.info(f"Combined symbols: {len(combined)} unique symbols (NASDAQ-100: {len(nasdaq)}, S&P 500: {len(sp500)})")
        return combined
    
    def _should_update(self) -> bool:
        """Check if we should update the symbol lists"""
        if not self.last_update:
            return True
        return (datetime.now() - self.last_update).total_seconds() > self.update_interval
    
    def _load_nasdaq_100_symbols(self):
        """Load NASDAQ-100 symbols from multiple sources"""
        logger.info("Loading NASDAQ-100 symbols...")
        
        # Try multiple sources in order of preference
        sources = [
            self._load_nasdaq_100_from_stockanalysis,
            self._load_nasdaq_100_from_wikipedia,
            self._load_nasdaq_100_from_nasdaq,
            self._load_nasdaq_100_from_fmp
        ]
        
        for source_func in sources:
            try:
                symbols = source_func()
                if symbols and len(symbols) >= 90:  # Should have at least 90 symbols
                    self.nasdaq_100_symbols = symbols
                    logger.info(f"Successfully loaded {len(symbols)} NASDAQ-100 symbols from {source_func.__name__}")
                    return
            except Exception as e:
                logger.warning(f"Failed to load NASDAQ-100 from {source_func.__name__}: {str(e)}")
                continue
        
        # Fallback to hardcoded list
        logger.warning("All sources failed, using fallback NASDAQ-100 list")
        self._use_nasdaq_100_fallback()
    
    def _load_sp_500_symbols(self):
        """Load S&P 500 symbols from multiple sources"""
        logger.info("Loading S&P 500 symbols...")
        
        # Try multiple sources in order of preference
        sources = [
            self._load_sp_500_from_wikipedia,
            self._load_sp_500_from_spglobal,
            self._load_sp_500_from_yahoo
        ]
        
        for source_func in sources:
            try:
                symbols = source_func()
                if symbols and len(symbols) >= 450:  # Should have at least 450 symbols
                    self.sp_500_symbols = symbols
                    logger.info(f"Successfully loaded {len(symbols)} S&P 500 symbols from {source_func.__name__}")
                    return
            except Exception as e:
                logger.warning(f"Failed to load S&P 500 from {source_func.__name__}: {str(e)}")
                continue
        
        # Fallback to hardcoded list
        logger.warning("All sources failed, using fallback S&P 500 list")
        self._use_sp_500_fallback()
    
    def _load_nasdaq_100_from_stockanalysis(self) -> List[str]:
        """Load NASDAQ-100 symbols from StockAnalysis.com (reliable backup source)"""
        try:
            logger.info("Loading NASDAQ-100 from StockAnalysis.com...")
            
            url = "https://stockanalysis.com/list/nasdaq-100-stocks/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML table
            tables = pd.read_html(StringIO(response.text))
            
            # Find the table with NASDAQ-100 constituents
            for table in tables:
                if 'Symbol' in table.columns:
                    symbols = table['Symbol'].dropna().tolist()
                    # Clean symbols (remove any non-alphabetic characters and convert to uppercase)
                    symbols = [str(s).strip().upper() for s in symbols if str(s).strip().isalpha()]
                    if len(symbols) >= 90:  # Should have around 100 symbols
                        logger.info(f"Successfully parsed {len(symbols)} symbols from StockAnalysis.com")
                        return symbols
            
            logger.warning("Could not find NASDAQ-100 table in StockAnalysis.com")
            return []
            
        except Exception as e:
            logger.error(f"Error loading NASDAQ-100 from StockAnalysis.com: {str(e)}")
            return []
    
    def _load_nasdaq_100_from_wikipedia(self) -> List[str]:
        """Load NASDAQ-100 symbols from Wikipedia"""
        try:
            url = "https://en.wikipedia.org/wiki/Nasdaq-100"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse the Wikipedia table
            tables = pd.read_html(StringIO(response.text))
            for table in tables:
                if 'Ticker' in table.columns or 'Symbol' in table.columns:
                    symbol_col = 'Ticker' if 'Ticker' in table.columns else 'Symbol'
                    symbols = table[symbol_col].dropna().tolist()
                    # Clean symbols (remove any non-alphabetic characters)
                    symbols = [str(s).strip().upper() for s in symbols if str(s).strip().isalpha()]
                    if len(symbols) >= 90:
                        return symbols
            
            return []
            
        except Exception as e:
            logger.error(f"Error loading NASDAQ-100 from Wikipedia: {str(e)}")
            return []
    
    def _load_nasdaq_100_from_nasdaq(self) -> List[str]:
        """Load NASDAQ-100 symbols from Nasdaq website"""
        try:
            url = "https://www.nasdaq.com/market-activity/quotes/nasdaq-ndx-index"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # This would require more sophisticated parsing
            # For now, return empty list to try next source
            return []
            
        except Exception as e:
            logger.error(f"Error loading NASDAQ-100 from Nasdaq: {str(e)}")
            return []
    
    def _redact_apikey(self, url: str) -> str:
        """Redact the apikey query parameter in a URL for logging"""
        return re.sub(r'(apikey=)[^&]+', r'\1[REDACTED]', url)

    def _load_nasdaq_100_from_fmp(self) -> List[str]:
        """Load NASDAQ-100 symbols from FMP API"""
        try:
            fmp_api_key = self.settings.fmp_api_key
            if not fmp_api_key or fmp_api_key == "DUMMY":
                return []
            url = f"https://financialmodelingprep.com/api/v3/nasdaq_constituent?apikey={fmp_api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            symbols = [item.get('symbol', '') for item in data if item.get('symbol')]
            return symbols
        except Exception as e:
            redacted_url = self._redact_apikey(url)
            logger.error(f"Error loading NASDAQ-100 from FMP: {str(e)} | URL: {redacted_url}")
            return []
    
    def _load_sp_500_from_wikipedia(self) -> List[str]:
        """Load S&P 500 symbols from Wikipedia"""
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse the Wikipedia table
            tables = pd.read_html(StringIO(response.text))
            for table in tables:
                if 'Symbol' in table.columns:
                    symbols = table['Symbol'].dropna().tolist()
                    # Clean symbols
                    symbols = [str(s).strip().upper() for s in symbols if str(s).strip().isalpha()]
                    if len(symbols) >= 450:
                        return symbols
            
            return []
            
        except Exception as e:
            logger.error(f"Error loading S&P 500 from Wikipedia: {str(e)}")
            return []
    
    def _load_sp_500_from_spglobal(self) -> List[str]:
        """Load S&P 500 symbols from S&P Global"""
        try:
            # S&P Global doesn't provide a public API for this
            # Would need to scrape their website or use a different approach
            return []
            
        except Exception as e:
            logger.error(f"Error loading S&P 500 from S&P Global: {str(e)}")
            return []
    
    def _load_sp_500_from_yahoo(self) -> List[str]:
        """Load S&P 500 symbols from Yahoo Finance"""
        try:
            # Yahoo Finance doesn't provide a direct API for index constituents
            # Would need to scrape or use a different approach
            return []
            
        except Exception as e:
            logger.error(f"Error loading S&P 500 from Yahoo: {str(e)}")
            return []
    
    def _use_nasdaq_100_fallback(self):
        """Use fallback NASDAQ-100 symbols"""
        self.nasdaq_100_symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX",
            "ADBE", "CRM", "PYPL", "INTC", "AMD", "QCOM", "AVGO", "TXN",
            "COST", "PEP", "CSCO", "TMUS", "ORLY", "ADP", "ISRG", "REGN",
            "VRTX", "GILD", "ABNB", "SNPS", "KLAC", "LRCX", "MU", "PANW",
            "CDNS", "MAR", "MELI", "ASML", "CHTR", "WDAY", "FTNT", "PAYX",
            "CTAS", "ROST", "ODFL", "FAST", "BIIB", "ALGN", "DXCM", "IDXX",
            "VRSK", "CPRT", "PCAR", "EXC"
        ]
    
    def _use_sp_500_fallback(self):
        """Use fallback S&P 500 symbols (top 100 by market cap)"""
        self.sp_500_symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "LLY",
            "TSLA", "UNH", "V", "XOM", "JNJ", "WMT", "JPM", "PG", "MA",
            "HD", "CVX", "MRK", "ABBV", "KO", "PEP", "AVGO", "COST",
            "PFE", "TMO", "BAC", "ACN", "DHR", "VZ", "ADBE", "WFC", "CRM",
            "ABT", "NKE", "PM", "TXN", "NEE", "RTX", "HON", "QCOM", "T",
            "UPS", "MS", "BMY", "SPGI", "INTC", "INTU", "AMD", "IBM",
            "GS", "UNP", "CAT", "AMGN", "ISRG", "PLD", "GE", "AMAT",
            "LMT", "SYK", "GILD", "ADI", "REGN", "VRTX", "PANW", "KLAC",
            "SNPS", "CDNS", "MU", "LRCX", "ASML", "CHTR", "WDAY", "FTNT",
            "PAYX", "CTAS", "ROST", "ODFL", "FAST", "BIIB", "ALGN", "DXCM",
            "IDXX", "VRSK", "CPRT", "PCAR", "EXC", "CMCSA", "NFLX", "ADP",
            "ORLY", "MAR", "MELI", "ABNB", "CSCO", "TMUS", "PEP", "COST"
        ]
    
    def update_symbols(self):
        """Force update of symbol lists"""
        self.last_update = None
        self._load_nasdaq_100_symbols()
        self._load_sp_500_symbols()
        self.last_update = datetime.now()
    
    def validate_symbol_coverage(self) -> Dict:
        """
        Validate that we're covering the most important stocks
        Returns validation results and recommendations
        """
        logger.info("Starting symbol coverage validation")
        
        validation_result = {
            'validation_success': False,
            'nasdaq_100_validation': {},
            'sp_500_validation': {},
            'coverage_issues': [],
            'recommendations': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Validate NASDAQ-100 coverage
            nasdaq_validation = self._validate_nasdaq_100_coverage()
            validation_result['nasdaq_100_validation'] = nasdaq_validation
            
            # Validate S&P 500 coverage
            sp500_validation = self._validate_sp_500_coverage()
            validation_result['sp_500_validation'] = sp500_validation
            
            # Check for major market cap stocks
            market_cap_validation = self._validate_market_cap_coverage()
            
            # Generate recommendations
            recommendations = self._generate_coverage_recommendations(
                nasdaq_validation, sp500_validation, market_cap_validation
            )
            validation_result['recommendations'] = recommendations
            
            # Check for coverage issues
            issues = self._identify_coverage_issues(
                nasdaq_validation, sp500_validation, market_cap_validation
            )
            validation_result['coverage_issues'] = issues
            
            validation_result['validation_success'] = True
            logger.info("Symbol coverage validation completed successfully")
            
        except Exception as e:
            logger.error(f"Symbol coverage validation failed: {str(e)}")
            validation_result['error'] = str(e)
        
        return validation_result
    
    def _validate_nasdaq_100_coverage(self) -> Dict:
        """Validate NASDAQ-100 symbol coverage"""
        current_symbols = set(self.get_nasdaq_100_symbols())
        
        # Define critical NASDAQ-100 stocks (top 20 by market cap)
        critical_nasdaq = {
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX",
            "ADBE", "CRM", "PYPL", "INTC", "AMD", "QCOM", "AVGO", "TXN",
            "COST", "PEP", "CSCO", "TMUS"
        }
        
        # Check coverage
        missing_critical = critical_nasdaq - current_symbols
        covered_critical = critical_nasdaq.intersection(current_symbols)
        
        # Validate count
        expected_count = 100
        actual_count = len(current_symbols)
        count_valid = 90 <= actual_count <= 110  # Allow some flexibility
        
        return {
            'total_symbols': actual_count,
            'expected_count': expected_count,
            'count_valid': count_valid,
            'critical_symbols_covered': len(covered_critical),
            'critical_symbols_total': len(critical_nasdaq),
            'missing_critical': list(missing_critical),
            'coverage_percentage': (len(covered_critical) / len(critical_nasdaq)) * 100
        }
    
    def _validate_sp_500_coverage(self) -> Dict:
        """Validate S&P 500 symbol coverage"""
        current_symbols = set(self.get_sp_500_symbols())
        
        # Define critical S&P 500 stocks (top 50 by market cap)
        critical_sp500 = {
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "LLY",
            "TSLA", "UNH", "V", "XOM", "JNJ", "WMT", "JPM", "PG", "MA",
            "HD", "CVX", "MRK", "ABBV", "KO", "PEP", "AVGO", "COST",
            "PFE", "TMO", "BAC", "ACN", "DHR", "VZ", "ADBE", "WFC", "CRM",
            "ABT", "NKE", "PM", "TXN", "NEE", "RTX", "HON", "QCOM", "T",
            "UPS", "MS", "BMY", "SPGI", "INTU", "IBM", "GS", "UNP"
        }
        
        # Check coverage
        missing_critical = critical_sp500 - current_symbols
        covered_critical = critical_sp500.intersection(current_symbols)
        
        # Validate count
        expected_count = 500
        actual_count = len(current_symbols)
        count_valid = 450 <= actual_count <= 550  # Allow some flexibility
        
        return {
            'total_symbols': actual_count,
            'expected_count': expected_count,
            'count_valid': count_valid,
            'critical_symbols_covered': len(covered_critical),
            'critical_symbols_total': len(critical_sp500),
            'missing_critical': list(missing_critical),
            'coverage_percentage': (len(covered_critical) / len(critical_sp500)) * 100
        }
    
    def _validate_market_cap_coverage(self) -> Dict:
        """Validate coverage of major market cap stocks"""
        all_symbols = set(self.get_all_symbols())
        
        # Top 100 stocks by market cap (approximate)
        top_100_market_cap = {
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "LLY",
            "TSLA", "UNH", "V", "XOM", "JNJ", "WMT", "JPM", "PG", "MA",
            "HD", "CVX", "MRK", "ABBV", "KO", "PEP", "AVGO", "COST",
            "PFE", "TMO", "BAC", "ACN", "DHR", "VZ", "ADBE", "WFC", "CRM",
            "ABT", "NKE", "PM", "TXN", "NEE", "RTX", "HON", "QCOM", "T",
            "UPS", "MS", "BMY", "SPGI", "INTC", "INTU", "AMD", "IBM",
            "GS", "UNP", "CAT", "AMGN", "ISRG", "PLD", "GE", "AMAT",
            "LMT", "SYK", "GILD", "ADI", "REGN", "VRTX", "PANW", "KLAC",
            "SNPS", "CDNS", "MU", "LRCX", "ASML", "CHTR", "WDAY", "FTNT",
            "PAYX", "CTAS", "ROST", "ODFL", "FAST", "BIIB", "ALGN", "DXCM",
            "IDXX", "VRSK", "CPRT", "PCAR", "EXC", "CMCSA", "NFLX", "ADP",
            "ORLY", "MAR", "MELI", "ABNB", "CSCO", "TMUS", "NFLX", "ADP"
        }
        
        # Check coverage
        missing_top_100 = top_100_market_cap - all_symbols
        covered_top_100 = top_100_market_cap.intersection(all_symbols)
        
        return {
            'top_100_covered': len(covered_top_100),
            'top_100_total': len(top_100_market_cap),
            'missing_top_100': list(missing_top_100),
            'coverage_percentage': (len(covered_top_100) / len(top_100_market_cap)) * 100
        }
    
    def _generate_coverage_recommendations(self, nasdaq_validation: Dict, 
                                         sp500_validation: Dict, 
                                         market_cap_validation: Dict) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # NASDAQ-100 recommendations
        if not nasdaq_validation.get('count_valid', False):
            recommendations.append(
                f"NASDAQ-100 count validation failed: {nasdaq_validation.get('total_symbols', 0)} symbols "
                f"(expected ~{nasdaq_validation.get('expected_count', 100)})"
            )
        
        if nasdaq_validation.get('coverage_percentage', 0) < 95:
            recommendations.append(
                f"NASDAQ-100 critical coverage low: {nasdaq_validation.get('coverage_percentage', 0):.1f}% "
                f"({nasdaq_validation.get('critical_symbols_covered', 0)}/{nasdaq_validation.get('critical_symbols_total', 0)})"
            )
        
        # S&P 500 recommendations
        if not sp500_validation.get('count_valid', False):
            recommendations.append(
                f"S&P 500 count validation failed: {sp500_validation.get('total_symbols', 0)} symbols "
                f"(expected ~{sp500_validation.get('expected_count', 500)})"
            )
        
        if sp500_validation.get('coverage_percentage', 0) < 95:
            recommendations.append(
                f"S&P 500 critical coverage low: {sp500_validation.get('coverage_percentage', 0):.1f}% "
                f"({sp500_validation.get('critical_symbols_covered', 0)}/{sp500_validation.get('critical_symbols_total', 0)})"
            )
        
        # Market cap recommendations
        if market_cap_validation.get('coverage_percentage', 0) < 90:
            recommendations.append(
                f"Top 100 market cap coverage low: {market_cap_validation.get('coverage_percentage', 0):.1f}% "
                f"({market_cap_validation.get('top_100_covered', 0)}/{market_cap_validation.get('top_100_total', 0)})"
            )
        
        # Missing critical symbols
        missing_nasdaq = nasdaq_validation.get('missing_critical', [])
        missing_sp500 = sp500_validation.get('missing_critical', [])
        
        if missing_nasdaq:
            recommendations.append(f"Missing critical NASDAQ-100 symbols: {', '.join(missing_nasdaq[:5])}")
        
        if missing_sp500:
            recommendations.append(f"Missing critical S&P 500 symbols: {', '.join(missing_sp500[:5])}")
        
        # If no issues, add positive feedback
        if not recommendations:
            recommendations.append("Symbol coverage validation passed - all critical stocks covered")
        
        return recommendations
    
    def _identify_coverage_issues(self, nasdaq_validation: Dict, 
                                sp500_validation: Dict, 
                                market_cap_validation: Dict) -> List[str]:
        """Identify specific coverage issues"""
        issues = []
        
        # Check for critical missing symbols
        missing_nasdaq = nasdaq_validation.get('missing_critical', [])
        missing_sp500 = sp500_validation.get('missing_critical', [])
        
        if missing_nasdaq:
            issues.append(f"Critical NASDAQ-100 symbols missing: {missing_nasdaq}")
        
        if missing_sp500:
            issues.append(f"Critical S&P 500 symbols missing: {missing_sp500}")
        
        # Check for count issues
        if not nasdaq_validation.get('count_valid', False):
            issues.append(f"NASDAQ-100 count issue: {nasdaq_validation.get('total_symbols', 0)} symbols")
        
        if not sp500_validation.get('count_valid', False):
            issues.append(f"S&P 500 count issue: {sp500_validation.get('total_symbols', 0)} symbols")
        
        # Check for low coverage
        if nasdaq_validation.get('coverage_percentage', 0) < 90:
            issues.append(f"NASDAQ-100 coverage below 90%: {nasdaq_validation.get('coverage_percentage', 0):.1f}%")
        
        if sp500_validation.get('coverage_percentage', 0) < 90:
            issues.append(f"S&P 500 coverage below 90%: {sp500_validation.get('coverage_percentage', 0):.1f}%")
        
        return issues
    
    def force_refresh_and_validate(self) -> Dict:
        """
        Force refresh symbol lists and validate coverage
        Useful for daily/weekly maintenance
        """
        logger.info("Forcing symbol refresh and validation")
        
        # Force update
        self.update_symbols()
        
        # Validate coverage
        validation_result = self.validate_symbol_coverage()
        
        # Log results
        if validation_result.get('validation_success'):
            logger.info("Symbol refresh and validation completed successfully")
            
            # Log coverage statistics
            nasdaq = validation_result.get('nasdaq_100_validation', {})
            sp500 = validation_result.get('sp_500_validation', {})
            market_cap = validation_result.get('market_cap_validation', {})
            
            logger.info(f"NASDAQ-100: {nasdaq.get('total_symbols', 0)} symbols, "
                       f"{nasdaq.get('coverage_percentage', 0):.1f}% critical coverage")
            logger.info(f"S&P 500: {sp500.get('total_symbols', 0)} symbols, "
                       f"{sp500.get('coverage_percentage', 0):.1f}% critical coverage")
            logger.info(f"Top 100 Market Cap: {market_cap.get('coverage_percentage', 0):.1f}% coverage")
            
            # Log any issues
            issues = validation_result.get('coverage_issues', [])
            if issues:
                logger.warning(f"Coverage issues found: {len(issues)}")
                for issue in issues:
                    logger.warning(f"  - {issue}")
            
            # Log recommendations
            recommendations = validation_result.get('recommendations', [])
            if recommendations:
                logger.info(f"Recommendations: {len(recommendations)}")
                for rec in recommendations:
                    logger.info(f"  - {rec}")
        else:
            logger.error("Symbol refresh and validation failed")
        
        return validation_result


# Global instance
symbol_loader = SymbolLoader() 