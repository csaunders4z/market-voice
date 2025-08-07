"""
Comprehensive data collector for Market Voices
Ensures complete coverage of NASDAQ-100 and S&P-500 stocks
"""
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from ..utils.logger import get_logger
from ..utils.cache import cached  # Add this import at the top

# Initialize logger
logger = get_logger("ComprehensiveCollector")
import os
import yfinance as yf
import requests

from ..config.settings import get_settings
from ..utils.rate_limiter import api_rate_limiter, rate_limiter
from .fmp_stock_data import fmp_stock_collector
from .news_collector import news_collector
from .economic_calendar import economic_calendar
# from .free_news_sources import free_news_collector  # Optional dependency
from .symbol_loader import symbol_loader


class ComprehensiveDataCollector:
    """Comprehensive data collector ensuring complete index coverage"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Load current symbol lists
        self.symbol_lists = self._load_symbol_lists()
    
    @cached(ttl_hours=12, key_prefix="top_movers")
    def _get_top_movers(self, all_stocks: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Identify top 5 winners and bottom 5 losers from stock data.
        Cached for 12 hours to avoid redundant processing.
        
        Args:
            all_stocks: List of stock data dictionaries
            
        Returns:
            Tuple of (top_winners, bottom_losers) lists
        """
        if not all_stocks:
            return [], []
            
        # Sort by percentage change
        sorted_stocks = sorted(all_stocks, key=lambda x: x.get('change_percent', 0), reverse=True)
        
        # Get top 5 winners and bottom 5 losers
        top_winners = sorted_stocks[:5]
        bottom_losers = sorted_stocks[-5:]
        
        logger.info(f"Identified {len(top_winners)} winners and {len(bottom_losers)} losers")
        return top_winners, bottom_losers
    
    def _load_symbol_lists(self) -> Dict:
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
        
        # First, collect basic data for all symbols to identify top movers
        logger.info("Collecting basic data to identify top movers...")
        basic_data_result = unified_collector.collect_basic_data(symbols=all_symbols, production_mode=production_mode)
        
        if not basic_data_result.get('collection_success'):
            logger.error("Failed to collect basic data for top movers identification")
            return basic_data_result
        
        # Get all stocks and identify top movers (cached for 12 hours)
        all_stocks = basic_data_result.get('all_data', [])
        top_winners, bottom_losers = self._get_top_movers(tuple(all_stocks))  # Convert to tuple for hashing
        top_movers = top_winners + bottom_losers
        top_mover_symbols = [stock['symbol'] for stock in top_movers]
        
        logger.info(f"Top movers: {', '.join(top_mover_symbols)}")
        
        # Now collect detailed data including news only for top movers
        logger.info("Collecting detailed data for top movers...")
        detailed_data = unified_collector.collect_detailed_data(
            symbols=top_mover_symbols, 
            production_mode=production_mode
        )
        
        if not detailed_data.get('collection_success', False):
            logger.error("Failed to collect detailed data for top movers")
            return detailed_data
        
        # Prepare the result with coverage information
        result = {
            'collection_success': True,
            'collection_timestamp': datetime.now().isoformat(),
            'symbols_analyzed': len(all_stocks),
            'top_winners': top_winners,
            'bottom_losers': bottom_losers,
            'all_data': all_stocks,
            'detailed_data': detailed_data,
            # Add index coverage information
            'index_coverage': {
                'sp500_total': len([s for s in all_stocks if s.get('symbol') in self.symbol_lists['sp500_symbols']]),
                'nasdaq100_total': len([s for s in all_stocks if s.get('symbol') in self.symbol_lists['nasdaq100_symbols']]),
                'sp500_analyzed': len([s for s in all_stocks if s.get('symbol') in self.symbol_lists['sp500_symbols']]),
                'nasdaq100_analyzed': len([s for s in all_stocks if s.get('symbol') in self.symbol_lists['nasdaq100_symbols']]),
                'sp500_coverage': len([s for s in all_stocks if s.get('symbol') in self.symbol_lists['sp500_symbols']]) / max(1, len(self.symbol_lists['sp500_symbols'])),
                'nasdaq100_coverage': len([s for s in all_stocks if s.get('symbol') in self.symbol_lists['nasdaq100_symbols']]) / max(1, len(self.symbol_lists['nasdaq100_symbols']))
            }
        }
        
        logger.info("Comprehensive data collection completed successfully")
        return result


# Global instance
comprehensive_collector = ComprehensiveDataCollector()    