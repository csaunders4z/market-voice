"""
News collection for Market Voices
Handles market and business news from multiple sources
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger
import os

from ..config.settings import get_settings


class NewsCollector:
    """Collects market and business news from multiple sources"""
    
    def __init__(self):
        self.settings = get_settings()
        self.news_api_key = self.settings.news_api_key
        self.rapidapi_key = os.getenv("BIZTOC_API_KEY", "")
        self.rapidapi_host = "biztoc.p.rapidapi.com"
        
    def get_newsapi_news(self, query: str = "NASDAQ", hours_back: int = 24) -> List[Dict]:
        """Get news from NewsAPI"""
        if self.news_api_key == "DUMMY":
            logger.info("Using dummy news data for test mode")
            return self._get_dummy_news()
            
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'from': (datetime.now() - timedelta(hours=hours_back)).isoformat(),
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': self.news_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            # Process and filter articles
            processed_articles = []
            for article in articles[:10]:  # Limit to top 10
                processed_articles.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'published_at': article.get('publishedAt', ''),
                    'relevance_score': self._calculate_relevance_score(article, query)
                })
            
            logger.info(f"Retrieved {len(processed_articles)} articles from NewsAPI")
            return processed_articles
            
        except Exception as e:
            logger.error(f"Error fetching NewsAPI data: {str(e)}")
            return []
    
    def get_biztoc_news(self, query: str = "NASDAQ", hours_back: int = 24) -> List[Dict]:
        """Get business news from Biztoc via RapidAPI"""
        if not self.rapidapi_key or self.rapidapi_key == "DUMMY":
            logger.info("No Biztoc API key provided, skipping Biztoc news")
            return []
            
        try:
            url = f"https://{self.rapidapi_host}/search"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": self.rapidapi_host
            }
            params = {
                "q": query,
                "limit": "10"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Biztoc API response structure: {type(data)}")
            logger.debug(f"Biztoc API response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Handle different possible response formats
            if isinstance(data, dict):
                articles = data.get('articles', [])
            elif isinstance(data, list):
                articles = data
            else:
                logger.warning(f"Unexpected Biztoc response format: {type(data)}")
                articles = []
            
            # Process articles
            processed_articles = []
            for article in articles:
                if isinstance(article, dict):
                    processed_articles.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'source': article.get('source', ''),
                        'published_at': article.get('published_at', ''),
                        'relevance_score': self._calculate_relevance_score(article, query)
                    })
            
            logger.info(f"Retrieved {len(processed_articles)} articles from Biztoc")
            return processed_articles
            
        except Exception as e:
            logger.error(f"Error fetching Biztoc data: {str(e)}")
            return []
    
    def get_company_news_summary(self, symbol: str, company_name: str, percent_change: float) -> str:
        """Get a concise news summary for a specific company"""
        try:
            # Only fetch news for significant moves (>3% or high volume)
            if abs(percent_change) < 3:
                return ""
            
            # Get company-specific news
            company_news = self.get_newsapi_news(symbol, 48)
            biztoc_company_news = self.get_biztoc_news(symbol, 48)
            
            # Combine and sort by relevance
            all_news = company_news + biztoc_company_news
            if not all_news:
                return ""
            
            # Sort by relevance score
            sorted_news = sorted(all_news, key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            # Take the most relevant news
            top_news = sorted_news[0]
            title = top_news.get('title', '')
            source = top_news.get('source', '')
            
            # Create a concise summary
            if title and source:
                return f"{title} (via {source})"
            elif title:
                return title
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Error getting news summary for {symbol}: {str(e)}")
            return ""
    
    def get_market_news(self, symbols: List[str] = None, stock_data: List[Dict] = None) -> Dict:
        """Get comprehensive market news for the day with enhanced company integration"""
        logger.info("Starting market news collection")
        
        if symbols is None:
            symbols = ["NASDAQ", "S&P 500", "stock market"]
        
        all_news = {
            'market_news': [],
            'company_news': {},
            'news_summaries': {},  # New field for stock-specific news summaries
            'collection_success': False,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Get general market news
            market_news = self.get_newsapi_news("NASDAQ stock market", 24)
            biztoc_news = self.get_biztoc_news("NASDAQ", 24)
            
            # Combine and deduplicate news
            combined_news = market_news + biztoc_news
            unique_news = self._deduplicate_news(combined_news)
            
            # Sort by relevance and recency
            sorted_news = sorted(unique_news, 
                               key=lambda x: (x.get('relevance_score', 0), x.get('published_at', '')), 
                               reverse=True)
            
            all_news['market_news'] = sorted_news[:15]  # Top 15 most relevant
            
            # Get company-specific news for top movers
            if symbols:
                for symbol in symbols[:5]:  # Top 5 symbols
                    company_news = self.get_newsapi_news(symbol, 48)
                    if company_news:
                        all_news['company_news'][symbol] = company_news[:3]  # Top 3 per company
            
            # Get news summaries for significant stock moves
            if stock_data:
                for stock in stock_data:
                    symbol = stock.get('symbol', '')
                    company_name = stock.get('company_name', '')
                    percent_change = stock.get('percent_change', 0)
                    
                    if symbol and abs(percent_change) >= 3:  # Significant moves
                        news_summary = self.get_company_news_summary(symbol, company_name, percent_change)
                        if news_summary:
                            all_news['news_summaries'][symbol] = news_summary
            
            all_news['collection_success'] = True
            logger.info(f"News collection completed. Market news: {len(all_news['market_news'])}, "
                       f"Company news for {len(all_news['company_news'])} companies, "
                       f"News summaries for {len(all_news['news_summaries'])} stocks")
            
        except Exception as e:
            logger.error(f"Error in news collection: {str(e)}")
            all_news['error'] = str(e)
        
        return all_news
    
    def _calculate_relevance_score(self, article: Dict, query: str) -> float:
        """Calculate relevance score for an article"""
        score = 0.0
        
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        query_terms = query.lower().split()
        
        # Check for query terms in title and description
        for term in query_terms:
            if term in title:
                score += 2.0
            if term in description:
                score += 1.0
        
        # Bonus for financial keywords
        financial_keywords = ['earnings', 'revenue', 'profit', 'stock', 'market', 'trading', 'investor']
        for keyword in financial_keywords:
            if keyword in title or keyword in description:
                score += 0.5
        
        return score
    
    def _deduplicate_news(self, news_list: List[Dict]) -> List[Dict]:
        """Remove duplicate news articles based on title similarity"""
        seen_titles = set()
        unique_news = []
        
        for article in news_list:
            title = article.get('title', '').lower()
            # Simple deduplication - could be improved with fuzzy matching
            if title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(article)
        
        return unique_news
    
    def _get_dummy_news(self) -> List[Dict]:
        """Generate dummy news for test mode"""
        return [
            {
                'title': 'NASDAQ-100 Shows Strong Performance Amid Tech Rally',
                'description': 'Technology stocks led the market higher as investors remain optimistic about AI and cloud computing growth.',
                'url': 'https://example.com/news1',
                'source': 'Financial Times',
                'published_at': datetime.now().isoformat(),
                'relevance_score': 8.5
            },
            {
                'title': 'Apple and Microsoft Lead Market Gains',
                'description': 'Major tech companies posted solid gains as quarterly earnings exceeded expectations.',
                'url': 'https://example.com/news2',
                'source': 'Reuters',
                'published_at': datetime.now().isoformat(),
                'relevance_score': 7.5
            },
            {
                'title': 'Market Volatility Expected as Fed Meeting Approaches',
                'description': 'Investors are closely watching the Federal Reserve for signals on future interest rate policy.',
                'url': 'https://example.com/news3',
                'source': 'Bloomberg',
                'published_at': datetime.now().isoformat(),
                'relevance_score': 6.5
            }
        ]


# Global instance
news_collector = NewsCollector() 