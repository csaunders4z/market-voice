"""
Comprehensive data collector for Market Voices
Ensures complete coverage of NASDAQ-100 and S&P-500 stocks
"""
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from loguru import logger
import os
import yfinance as yf
import requests

from ..config.settings import get_settings
from ..utils.rate_limiter import api_rate_limiter, rate_limiter
from .fmp_stock_data import fmp_stock_collector
from .news_collector import news_collector
from .economic_calendar import economic_calendar
from .free_news_sources import free_news_collector
from .symbol_loader import symbol_loader


class ComprehensiveDataCollector:
    """Comprehensive data collector ensuring complete index coverage"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Load current symbol lists
        self.symbol_lists = self._load_symbol_lists()
        
    def _load_symbol_lists(self) -> Dict[str, List[str]]:
        """Load current symbol lists from symbol loader"""
        try:
            # Get symbols from symbol loader
            all_symbols = symbol_loader.get_all_symbols()
            sp500_symbols = symbol_loader.get_sp_500_symbols()
            nasdaq100_symbols = symbol_loader.get_nasdaq_100_symbols()
            
            logger.info(f"Loaded symbol lists: {len(sp500_symbols)} S&P 500, {len(nasdaq100_symbols)} NASDAQ-100, {len(all_symbols)} total unique")
            
            return {
                'all_symbols': all_symbols,
                'sp500_symbols': sp500_symbols,
                'nasdaq100_symbols': nasdaq100_symbols,
                'sp500_count': len(sp500_symbols),
                'nasdaq100_count': len(nasdaq100_symbols)
            }
        except Exception as e:
            logger.error(f"Failed to load symbol lists: {str(e)}")
            # Fallback to FMP collector symbols
            return {
                'all_symbols': fmp_stock_collector.symbols,
                'sp500_symbols': fmp_stock_collector.symbols,
                'nasdaq100_symbols': fmp_stock_collector.symbols,
                'sp500_count': len(fmp_stock_collector.symbols),
                'nasdaq100_count': len(fmp_stock_collector.symbols)
            }
    
    def collect_comprehensive_data(self, production_mode: bool = True) -> Dict:
        """Collect data for ALL NASDAQ-100 and S&P-500 stocks"""
        logger.info("Starting comprehensive data collection for ALL NASDAQ-100 and S&P-500 stocks")
        
        # Get all symbols we need to collect
        all_symbols = self.symbol_lists.get('all_symbols', [])
        sp500_symbols = self.symbol_lists.get('sp500_symbols', [])
        nasdaq100_symbols = self.symbol_lists.get('nasdaq100_symbols', [])
        
        logger.info(f"Target coverage:")
        logger.info(f"  Total unique symbols: {len(all_symbols)}")
        logger.info(f"  S&P 500 symbols: {len(sp500_symbols)}")
        logger.info(f"  NASDAQ-100 symbols: {len(nasdaq100_symbols)}")
        
        # For now, use the existing unified collector but with all symbols
        from .unified_data_collector import unified_collector
        
        # Override the symbols to use all symbols
        original_symbols = fmp_stock_collector.symbols
        fmp_stock_collector.symbols = all_symbols
        
        try:
            result = unified_collector.collect_data(symbols=all_symbols, production_mode=production_mode)
            
            # Add coverage statistics
            if result.get('collection_success'):
                total_coverage = len(result.get('all_data', []))
                sp500_coverage = len([s for s in result.get('all_data', []) if s['symbol'] in sp500_symbols])
                nasdaq100_coverage = len([s for s in result.get('all_data', []) if s['symbol'] in nasdaq100_symbols])
                
                result['coverage_stats'] = {
                    'total_coverage': total_coverage,
                    'sp500_coverage': sp500_coverage,
                    'nasdaq100_coverage': nasdaq100_coverage,
                    'coverage_percentage': (total_coverage / len(all_symbols)) * 100 if all_symbols else 0
                }
                
                # Update market summary
                if 'market_summary' in result:
                    result['market_summary']['total_target_symbols'] = len(all_symbols)
                    result['market_summary']['sp500_coverage'] = sp500_coverage
                    result['market_summary']['nasdaq100_coverage'] = nasdaq100_coverage
                    result['market_summary']['coverage_percentage'] = (total_coverage / len(all_symbols)) * 100 if all_symbols else 0
                    result['market_summary']['market_coverage'] = f"Analyzing {total_coverage}/{len(all_symbols)} NASDAQ-100 and S&P-500 stocks ({total_coverage/len(all_symbols)*100:.1f}% coverage)"
            
            return result
            
        finally:
            # Restore original symbols
            fmp_stock_collector.symbols = original_symbols


# Global instance
comprehensive_collector = ComprehensiveDataCollector() 