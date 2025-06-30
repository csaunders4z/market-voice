"""
Two-Phase Data Collector for Market Voices
Implements the original plan: Phase 1 (screening) → Phase 2 (deep analysis)
"""
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from .screening_module import screening_module
from .deep_analysis_module import deep_analysis_module
from .news_collector import news_collector
from .free_news_sources import free_news_collector
from .economic_calendar import economic_calendar
from ..config.settings import get_settings


class TwoPhaseCollector:
    """Implements two-phase data collection workflow"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def collect_data(self, max_symbols: int = None) -> Dict:
        """
        Execute two-phase data collection workflow:
        Phase 1: Screen all symbols to identify top movers
        Phase 2: Deep analysis only for identified top movers
        """
        logger.info("Starting Two-Phase Data Collection Workflow")
        logger.info("=" * 60)
        
        # Phase 1: Screening
        logger.info("PHASE 1: SYMBOL SCREENING")
        logger.info("-" * 40)
        
        screening_result = screening_module.screen_symbols(max_symbols=max_symbols)
        
        if not screening_result.get('screening_success'):
            logger.error(f"Screening failed: {screening_result.get('error', 'Unknown error')}")
            return {
                'collection_success': False,
                'error': f"Screening phase failed: {screening_result.get('error')}",
                'timestamp': datetime.now().isoformat()
            }
        
        # Log screening results
        winners = screening_result.get('winners', [])
        losers = screening_result.get('losers', [])
        total_screened = screening_result.get('total_screened', 0)
        data_source = screening_result.get('data_source', 'Unknown')
        
        logger.info(f"✅ Screening completed successfully!")
        logger.info(f"   Data source: {data_source}")
        logger.info(f"   Total symbols screened: {total_screened}")
        logger.info(f"   Top winners identified: {len(winners)}")
        logger.info(f"   Top losers identified: {len(losers)}")
        
        if winners:
            logger.info(f"   Top winners: {[w.get('symbol') for w in winners]}")
        if losers:
            logger.info(f"   Top losers: {[l.get('symbol') for l in losers]}")
        
        # Phase 2: Deep Analysis
        logger.info("\nPHASE 2: DEEP ANALYSIS")
        logger.info("-" * 40)
        
        if not winners and not losers:
            logger.warning("No top movers identified, skipping deep analysis")
            return {
                'collection_success': False,
                'error': 'No top movers identified during screening',
                'timestamp': datetime.now().isoformat()
            }
        
        analysis_result = deep_analysis_module.analyze_top_movers(winners, losers)
        
        if not analysis_result.get('analysis_success'):
            logger.error("Deep analysis failed")
            return {
                'collection_success': False,
                'error': 'Deep analysis phase failed',
                'timestamp': datetime.now().isoformat()
            }
        
        # Log analysis results
        analyzed_winners = analysis_result.get('analyzed_winners', [])
        analyzed_losers = analysis_result.get('analyzed_losers', [])
        total_analyzed = analysis_result.get('total_analyzed', 0)
        
        logger.info(f"✅ Deep analysis completed successfully!")
        logger.info(f"   Total stocks analyzed: {total_analyzed}")
        logger.info(f"   Winners with deep data: {len(analyzed_winners)}")
        logger.info(f"   Losers with deep data: {len(analyzed_losers)}")
        
        # Phase 3: Market Context (News, Economic Calendar)
        logger.info("\nPHASE 3: MARKET CONTEXT")
        logger.info("-" * 40)
        
        # Get economic calendar data
        economic_data = None
        try:
            economic_data = economic_calendar.get_comprehensive_calendar()
            logger.info("✅ Economic calendar data collected")
        except Exception as e:
            logger.warning(f"Failed to get economic calendar data: {str(e)}")
        
        # Get market news
        market_news = None
        try:
            # Get news for top movers
            top_symbols = [stock.get('symbol') for stock in analyzed_winners + analyzed_losers]
            market_news = news_collector.get_market_news(symbols=top_symbols)
            logger.info("✅ Market news data collected")
        except Exception as e:
            logger.warning(f"Failed to get market news: {str(e)}")
        
        # Get free news as backup
        free_news = None
        try:
            free_news = free_news_collector.get_comprehensive_free_news("NASDAQ stock market", 10)
            if free_news:
                logger.info(f"✅ Free news collected: {len(free_news)} articles")
        except Exception as e:
            logger.warning(f"Failed to get free news: {str(e)}")
        
        # Create comprehensive market summary
        market_summary = self._create_market_summary(
            analyzed_winners, analyzed_losers, total_screened, 
            data_source, economic_data, market_news, free_news
        )
        
        # Final result
        result = {
            'collection_success': True,
            'workflow_phases': {
                'phase_1_screening': screening_result,
                'phase_2_analysis': analysis_result,
                'phase_3_context': {
                    'economic_data': economic_data is not None,
                    'market_news': market_news is not None,
                    'free_news': free_news is not None
                }
            },
            'market_summary': market_summary,
            'winners': analyzed_winners,
            'losers': analyzed_losers,
            'all_screened_data': screening_result.get('screened_data', []),
            'data_source': data_source,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ TWO-PHASE DATA COLLECTION COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"   Screening: {total_screened} symbols → {len(winners + losers)} top movers")
        logger.info(f"   Deep Analysis: {total_analyzed} stocks with detailed data")
        logger.info(f"   Market Context: Economic calendar + News data")
        logger.info(f"   Data Source: {data_source}")
        
        return result
    
    def _create_market_summary(self, winners: List[Dict], losers: List[Dict], 
                              total_screened: int, data_source: str,
                              economic_data: Dict, market_news: Dict, 
                              free_news: List[Dict]) -> Dict:
        """Create comprehensive market summary"""
        
        # Calculate market statistics
        all_movers = winners + losers
        advancing_stocks = len([s for s in all_movers if s.get('percent_change', 0) > 0])
        declining_stocks = len([s for s in all_movers if s.get('percent_change', 0) < 0])
        
        if all_movers:
            average_change = sum(s.get('percent_change', 0) for s in all_movers) / len(all_movers)
        else:
            average_change = 0
        
        # Determine market sentiment
        if advancing_stocks > declining_stocks * 1.5 and average_change > 1:
            sentiment = "Bullish"
        elif declining_stocks > advancing_stocks * 1.5 and average_change < -1:
            sentiment = "Bearish"
        else:
            sentiment = "Mixed"
        
        # Create summary
        summary = {
            'total_stocks_screened': total_screened,
            'total_top_movers': len(all_movers),
            'advancing_stocks': advancing_stocks,
            'declining_stocks': declining_stocks,
            'average_change': round(average_change, 2),
            'market_sentiment': sentiment,
            'market_date': datetime.now().isoformat(),
            'collection_timestamp': datetime.now().isoformat(),
            'data_source': data_source,
            'workflow_type': 'Two-Phase Collection',
            'market_coverage': f"Analyzing {len(all_movers)} top movers from {total_screened} screened stocks"
        }
        
        # Add context data
        if economic_data:
            summary['economic_calendar'] = economic_data
        
        if market_news:
            summary['market_news'] = market_news
        
        if free_news:
            summary['free_news'] = {
                'articles': free_news,
                'article_count': len(free_news),
                'sources': list(set(article.get('source', '') for article in free_news)),
                'timestamp': datetime.now().isoformat()
            }
        
        return summary


# Global instance
two_phase_collector = TwoPhaseCollector() 