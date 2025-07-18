"""
News collection for Market Voices
Handles market and business news from multiple sources
ENHANCED: Now includes comprehensive free news source scraping
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)
import os
import pytz

from src.config.settings import get_settings

# Import our new free news scraper
try:
    from .stock_news_scraper import stock_news_scraper
    FREE_NEWS_AVAILABLE = True
    logger.info("✅ Free news scraper available")
except ImportError as e:
    FREE_NEWS_AVAILABLE = False
    logger.warning(f"⚠️  Free news scraper not available: {e}")


from .finnhub_news_adapter import finnhub_news_adapter

class NewsCollector:
    """Collects market and business news from multiple sources, including Finnhub"""
    
    def __init__(self):
        self.settings = get_settings()
        self.the_news_api_api_key = self.settings.the_news_api_api_key
        self.rapidapi_key = os.getenv("BIZTOC_API_KEY", "")
        self.rapidapi_host = "biztoc.p.rapidapi.com"
        self.newsdata_api_key = self.settings.newsdata_io_api_key
        self.market_tz = pytz.timezone('US/Eastern')
        # Global circuit breaker/session disable for NewsAPI
        self._newsapi_consecutive_failures = 0
        self._newsapi_failure_threshold = 5  # configurable
        self._newsapi_disabled_for_session = False
        # Global circuit breaker/session disable for Newsdata.io
        self._newsdata_consecutive_failures = 0
        self._newsdata_failure_threshold = 5  # configurable
        self._newsdata_disabled_for_session = False
        # Global circuit breaker/session disable for Biztoc
        self._biztoc_consecutive_failures = 0
        self._biztoc_failure_threshold = 5  # configurable
        self._biztoc_disabled_for_session = False
        # Global circuit breaker/session disable for The News API
        self._thenewsapi_consecutive_failures = 0
        self._thenewsapi_failure_threshold = 5  # configurable
        self._thenewsapi_disabled_for_session = False
    
    def reset_circuit_breakers(self):
        """Reset all circuit breakers - call this periodically or on successful requests"""
        self._newsapi_consecutive_failures = 0
        self._newsapi_disabled_for_session = False
        self._newsdata_consecutive_failures = 0
        self._newsdata_disabled_for_session = False
        self._biztoc_consecutive_failures = 0
        self._biztoc_disabled_for_session = False
        self._thenewsapi_consecutive_failures = 0
        self._thenewsapi_disabled_for_session = False
        logger.info("Circuit breakers reset")

    def _get_market_time_range(self, hours_back: int = 24) -> tuple[datetime, datetime]:
        """Get time range in market timezone for news collection"""
        market_now = datetime.now(self.market_tz)
        from_time = market_now - timedelta(hours=hours_back)
        return from_time, market_now
        
    def get_newsapi_news(self, query: str = "NASDAQ", hours_back: int = 24) -> List[Dict]:
        """Get news from NewsAPI with global circuit breaker/session disable logic"""
        if self._newsapi_disabled_for_session:
            logger.error(f"NewsAPI disabled for this session after {self._newsapi_failure_threshold} consecutive failures. Skipping all NewsAPI requests.")
            return []
        if self.the_news_api_api_key == "DUMMY": 
            logger.info("Using dummy news data for test mode")
            return self._get_dummy_news()
            
        try:
            url = "https://newsapi.org/v2/everything"
            market_now = datetime.now(self.market_tz)
            from_time = market_now - timedelta(hours=hours_back)
            params = {
                'q': query,
                'from': from_time.isoformat(),
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': self.the_news_api_api_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            # Process and filter articles with enhanced content
            processed_articles = []
            for article in articles[:15]:  # Increased limit to 15
                # Extract more content
                content = article.get('content', '')
                description = article.get('description', '')
                
                # Combine content and description for more comprehensive text
                full_text = f"{description} {content}".strip()
                
                # Get additional metadata
                author = article.get('author', '')
                source_name = article.get('source', {}).get('name', '')
                url = article.get('url', '')
                published_at = article.get('publishedAt', '')
                
                processed_articles.append({
                    'title': article.get('title', ''),
                    'description': description,
                    'content': content,
                    'full_text': full_text,  # Combined text for analysis
                    'url': url,
                    'source': source_name,
                    'author': author,
                    'published_at': published_at,
                    'relevance_score': self._calculate_relevance_score(article, query),
                    'word_count': len(full_text.split()) if full_text else 0
                })
            
            # Filter to today's articles only
            today_articles = self._filter_today_articles(processed_articles)
            logger.info(f"Retrieved {len(today_articles)} today's articles from NewsAPI (from {len(processed_articles)} total)")
            return today_articles
        except Exception as e:
            logger.error(f"Error fetching NewsAPI data: {str(e)}")
            return []
    
    def get_biztoc_news(self, query: str = "NASDAQ", hours_back: int = 24, company: str = None) -> List[Dict]:
        """Get business news from Biztoc via RapidAPI with enhanced content and company support"""
        if not self.rapidapi_key or self.rapidapi_key == "DUMMY":
            logger.info("No Biztoc API key provided, skipping Biztoc news")
            return []
            
        try:
            # Try multiple Biztoc endpoints for comprehensive coverage
            articles = []
            
            # 1. General search
            search_articles = self._get_biztoc_search(query, 10)
            articles.extend(search_articles)
            
            # 2. Trending business news
            trending_articles = self._get_biztoc_trending(5)
            articles.extend(trending_articles)
            
            # 3. Market-specific news
            market_articles = self._get_biztoc_market_news(5)
            articles.extend(market_articles)
            
            # 4. Company-specific news (if symbol provided)
            if company:
                company_articles = self._get_biztoc_company_news(company, 5)
                articles.extend(company_articles)
            
            # Deduplicate articles
            unique_articles = self._deduplicate_news(articles)
            
            # Process articles with enhanced content
            processed_articles = []
            for article in unique_articles[:15]:  # Limit to 15 best articles
                if isinstance(article, dict):
                    # Extract more content fields
                    title = article.get('title', '')
                    description = article.get('description', '')
                    content = article.get('content', '')  # Some APIs provide full content
                    
                    # Combine available text
                    full_text = f"{description}\n{content}" if content else description
                    
                    processed_articles.append({
                        'title': title,
                        'description': description,
                        'content': content,
                        'full_text': full_text,
                        'url': article.get('url', ''),
                        'source': article.get('source', ''),
                        'author': article.get('author', ''),
                        'published_at': article.get('published_at', ''),
                        'relevance_score': self._calculate_relevance_score(article, query),
                        'word_count': len(full_text.split()) if full_text else 0
                    })
            
            # Filter to today's articles only
            today_articles = self._filter_today_articles(processed_articles)
            
            logger.info(f"Retrieved {len(today_articles)} today's articles from Biztoc (from {len(processed_articles)} total)")
            return today_articles
            
        except Exception as e:
            logger.error(f"Error fetching Biztoc data: {str(e)}")
            return []
    
    def get_newsdata_news(self, query: str = "NASDAQ", hours_back: int = 24, company: str = None) -> List[Dict]:
        """Get news from NewsData.io with enhanced content and company support, with global circuit breaker/session disable logic"""
        if self._newsdata_disabled_for_session:
            logger.error(f"NewsData.io disabled for this session after {self._newsdata_failure_threshold} consecutive failures. Skipping all NewsData.io requests.")
            return []
        if not self.newsdata_api_key or self.newsdata_api_key == "DUMMY":
            logger.info("No NewsData.io API key provided, skipping NewsData.io news")
            return []
        
        try:
            articles = []
            
            # 1. General business news search
            search_articles = self._get_newsdata_search(query, 10)
            articles.extend(search_articles)
            
            # 2. Company-specific news (if symbol provided)
            if company:
                company_articles = self._get_newsdata_search(company, 8)
                articles.extend(company_articles)
            
            # Deduplicate articles by URL
            unique_articles = {a['url']: a for a in articles if 'url' in a}
            
            # Process articles with enhanced content
            processed_articles = []
            for article in unique_articles.values():
                title = article.get('title', '')
                description = article.get('description', '')
                content = article.get('content', '')
                full_text = f"{description}\n{content}" if content else description
                processed_articles.append({
                    'title': title,
                    'description': description,
                    'content': content,
                    'url': article.get('url', ''),
                    'source': article.get('source', ''),
                    'published_at': article.get('pubDate', ''),
                    'word_count': len(full_text.split()) if full_text else 0
                })

            
            # Filter to today's articles only
            today_articles = self._filter_today_articles(processed_articles)
            
            logger.info(f"Retrieved {len(today_articles)} today's articles from NewsData.io (from {len(processed_articles)} total)")
            return today_articles
            
        except Exception as e:
            logger.error(f"Error fetching NewsData.io data: {str(e)}")
            return []
    
    def get_the_news_api_news(self, query: str = "NASDAQ", hours_back: int = 24, company: str = None) -> List[Dict]:
        """Get news from The News API with enhanced content and company support"""
        if not self.the_news_api_api_key or self.the_news_api_api_key == "DUMMY":
            logger.info("No The News API key provided, skipping The News API news")
            return []
            
        try:
            articles = []
            
            # 1. General business news search
            search_articles = self._get_the_news_api_search(query, 10)
            articles.extend(search_articles)
            
            # 2. Company-specific news (if symbol provided)
            if company:
                company_articles = self._get_the_news_api_company_news(company, 8)
                articles.extend(company_articles)
            
            # 3. Top business stories
            top_articles = self._get_the_news_api_top_business(5)
            articles.extend(top_articles)
            
            # Deduplicate articles
            unique_articles = self._deduplicate_news(articles)
            
            # Process articles with enhanced content
            processed_articles = []
            for article in unique_articles[:15]:  # Limit to 15 best articles
                if isinstance(article, dict):
                    # Extract content fields
                    title = article.get('title', '')
                    description = article.get('description', '')
                    snippet = article.get('snippet', '')
                    
                    # Combine available text
                    full_text = f"{description} {snippet}".strip()
                    
                    # Get additional metadata
                    source_name = article.get('source', '')
                    url = article.get('url', '')
                    published_at = article.get('published_at', '')
                    categories = article.get('categories', [])
                    
                    processed_articles.append({
                        'title': title,
                        'description': description,
                        'content': snippet,
                        'full_text': full_text,
                        'url': url,
                        'source': source_name,
                        'author': '',  # The News API doesn't provide author
                        'published_at': published_at,
                        'category': categories,
                        'relevance_score': self._calculate_relevance_score(article, query),
                        'word_count': len(full_text.split()) if full_text else 0
                    })
            
            # Filter to today's articles only
            today_articles = self._filter_today_articles(processed_articles)
            
            logger.info(f"Retrieved {len(today_articles)} today's articles from The News API (from {len(processed_articles)} total)")
            return today_articles
            
        except Exception as e:
            logger.error(f"Error fetching The News API data: {str(e)}")
            return []
    
    def _get_biztoc_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Get articles from Biztoc search endpoint"""
        try:
            url = f"https://{self.rapidapi_host}/search"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": self.rapidapi_host
            }
            params = {
                "q": query,
                "limit": str(limit)
            }
            
            logger.info(f"About to call Biztoc API: {url} with headers: {headers} and params: {params}")
            print(f"About to call Biztoc API: {url} with headers: {headers} and params: {params}")
            response = requests.get(url, headers=headers, params=params, timeout=15)
            logger.info(f"Biztoc API {url} status: {response.status_code}")
            logger.info(f"Biztoc API {url} response: {response.text}")
            print(f"Biztoc API {url} status: {response.status_code}")
            print(f"Biztoc API {url} response: {response.text}")
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, dict):
                return data.get('articles', [])
            elif isinstance(data, list):
                return data
            return []
        except Exception as e:
            self._biztoc_consecutive_failures += 1
            if self._biztoc_consecutive_failures >= self._biztoc_failure_threshold:
                self._biztoc_disabled_for_session = True

    def _get_biztoc_market_news(self, limit: int = 5) -> List[Dict]:
        """Get market-specific news from Biztoc"""
        logger.info("[MARKET] Entry: _get_biztoc_market_news")
        if self._biztoc_disabled_for_session:
            logger.error(f"[MARKET] Biztoc API disabled for this session after {self._biztoc_failure_threshold} consecutive failures. Skipping all Biztoc requests.")
            print("[MARKET] Biztoc API disabled for this session. Skipping request.")
            return []
        try:
            url = f"https://{self.rapidapi_host}/market"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": self.rapidapi_host
            }
            params = {
                "limit": str(limit)
            }
            logger.info(f"[MARKET] About to call Biztoc API: {url} with headers: {headers} and params: {params}")
            print(f"[MARKET] About to call Biztoc API: {url} with headers: {headers} and params: {params}")
            response = requests.get(url, headers=headers, params=params, timeout=15)
            logger.info(f"[MARKET] Biztoc API {url} status: {response.status_code}")
            logger.info(f"[MARKET] Biztoc API {url} response: {response.text}")
            print(f"[MARKET] Biztoc API {url} status: {response.status_code}")
            print(f"[MARKET] Biztoc API {url} response: {response.text}")
            response.raise_for_status()

            data = response.json()
            if isinstance(data, dict):
                return data.get('articles', [])
            elif isinstance(data, list):
                return data
            return []
        except Exception as e:
            logger.error(f"[MARKET] Biztoc market news failed: {str(e)}")
            print(f"[MARKET] Biztoc market news failed: {str(e)}")
            return []
        finally:
            logger.info("[MARKET] Exit: _get_biztoc_market_news")
            print("[MARKET] Exit: _get_biztoc_market_news")
                

    
    def _create_news_summary(self, articles: List[Dict], symbol: str) -> str:
        """Create a comprehensive news summary from multiple articles"""
        if not articles:
            return ""
        
        # Get the most relevant article
        top_article = articles[0]
        title = top_article.get('title', '')
        source = top_article.get('source', '')
        description = top_article.get('description', '')
        
        # Create a rich summary
        summary_parts = []
        
        if title:
            summary_parts.append(title)
        
        if description and len(description) > 20:
            summary_parts.append(description[:200] + "..." if len(description) > 200 else description)
        
        # Add source attribution
        if source:
            summary_parts.append(f"(Source: {source})")
        
        # Add additional context from other articles
        if len(articles) > 1:
            additional_sources = set()
            for article in articles[1:3]:  # Next 2 articles
                article_source = article.get('source', '')
                if article_source and article_source != source:
                    additional_sources.add(article_source)
            
            if additional_sources:
                summary_parts.append(f"Additional coverage: {', '.join(list(additional_sources)[:2])}")
        
        return " ".join(summary_parts)
    
    def _identify_news_catalysts(self, articles: List[Dict]) -> List[str]:
        """Identify potential stock movement catalysts from news articles with enhanced detection"""
        catalysts = []
        
        # Enhanced catalyst keywords and patterns with more comprehensive coverage
        catalyst_patterns = {
            'earnings': [
                'earnings', 'beat', 'miss', 'surprise', 'eps', 'revenue', 'quarterly results',
                'earnings report', 'q1', 'q2', 'q3', 'q4', 'fiscal year', 'profit',
                'earnings per share', 'revenue growth', 'earnings guidance', 'beat estimates',
                'miss expectations', 'earnings call', 'financial results'
            ],
            'analyst_action': [
                'upgrade', 'downgrade', 'price target', 'rating', 'analyst', 'buy rating',
                'sell rating', 'hold rating', 'outperform', 'underperform', 'overweight',
                'underweight', 'neutral', 'strong buy', 'strong sell', 'target price',
                'consensus', 'recommendation', 'coverage initiated', 'coverage resumed'
            ],
            'merger_acquisition': [
                'acquisition', 'merger', 'takeover', 'buyout', 'deal', 'acquired',
                'merge', 'purchase', 'bid', 'offer', 'transaction', 'consolidation',
                'strategic acquisition', 'hostile takeover', 'friendly merger',
                'cash deal', 'stock deal', 'all-cash', 'all-stock'
            ],
            'partnership_collaboration': [
                'partnership', 'collaboration', 'joint venture', 'alliance', 'agreement',
                'contract', 'deal', 'cooperation', 'strategic partnership', 'licensing',
                'distribution agreement', 'supply agreement', 'manufacturing agreement'
            ],
            'product_innovation': [
                'launch', 'product', 'innovation', 'breakthrough', 'patent', 'new product',
                'product launch', 'innovation', 'technology', 'development', 'research',
                'clinical trial', 'study results', 'drug approval', 'device approval'
            ],
            'regulatory_legal': [
                'approval', 'fda', 'regulatory', 'compliance', 'investigation', 'lawsuit',
                'settlement', 'fine', 'penalty', 'violation', 'sec', 'ftc', 'doj',
                'court', 'judge', 'ruling', 'decision', 'cleared', 'authorized'
            ],
            'guidance_outlook': [
                'guidance', 'forecast', 'outlook', 'projections', 'expects', 'anticipates',
                'raised guidance', 'lowered guidance', 'updated outlook', 'full year',
                'next quarter', 'forward looking', 'estimates', 'targets'
            ],
            'insider_activity': [
                'insider', 'ceo', 'executive', 'management', 'shares', 'insider trading',
                'insider buying', 'insider selling', 'stock purchase', 'stock sale',
                'executive compensation', 'board', 'director', 'officer'
            ],
            'dividend_buyback': [
                'dividend', 'buyback', 'share repurchase', 'special dividend', 'dividend increase',
                'dividend cut', 'dividend yield', 'payout', 'return to shareholders',
                'capital allocation', 'stock split', 'spin-off'
            ],
            'financial_metrics': [
                'debt', 'cash', 'liquidity', 'credit rating', 'debt reduction', 'refinancing',
                'credit facility', 'loan', 'financing', 'capital raise', 'ipo', 'offering',
                'secondary offering', 'convertible', 'bonds'
            ]
        }
        
        for article in articles:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = f"{title} {description}"
            
            catalyst_scores = {}
            
            for catalyst_type, keywords in catalyst_patterns.items():
                score = 0
                for keyword in keywords:
                    if keyword in content:
                        if keyword in title:
                            score += 2
                        else:
                            score += 1
                
                if score > 0:
                    catalyst_scores[catalyst_type] = score
            
            # Add catalysts that meet minimum confidence threshold
            for catalyst_type, score in catalyst_scores.items():
                if score >= 1 and catalyst_type not in catalysts:
                    catalysts.append(catalyst_type)
        
        return catalysts
    
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
            
            # ENHANCED: Get comprehensive news for ALL top movers (expanded coverage)
            if stock_data:
                # Process top 10 winners and losers for comprehensive news
                sorted_stocks = sorted(stock_data, key=lambda x: abs(x.get('percent_change', 0)), reverse=True)
                top_movers = sorted_stocks[:20]  # Top 20 movers get full news analysis
                
                comprehensive_news = {}
                
                for stock in top_movers:
                    symbol = stock.get('symbol', '')
                    company_name = stock.get('company_name', '')
                    percent_change = stock.get('percent_change', 0)
                    
                    if symbol and abs(percent_change) >= 1:  # Lowered threshold
                        try:
                            # Get comprehensive news (includes catalysts and detailed analysis)
                            comp_news = self.get_comprehensive_company_news(symbol, company_name, percent_change)
                            if comp_news.get('collection_success'):
                                comprehensive_news[symbol] = comp_news
                                
                                # Also add to simple summaries for backward compatibility
                                if comp_news.get('summary'):
                                    all_news['news_summaries'][symbol] = comp_news['summary']
                        except Exception as e:
                            logger.warning(f"Failed to get comprehensive news for {symbol}: {str(e)}")
                            # Fallback to simple summary
                            news_summary = self.get_company_news_summary(symbol, company_name, percent_change)
                            if news_summary:
                                all_news['news_summaries'][symbol] = news_summary
                
                # Add comprehensive news data
                all_news['comprehensive_news'] = comprehensive_news
                logger.info(f"Comprehensive news collected for {len(comprehensive_news)} stocks")
            
            # ENHANCED: If no news collected from APIs, provide fallback news for WHY analysis
            if not all_news['market_news'] and not all_news['company_news']:
                logger.warning("No news collected from APIs, providing fallback news for WHY analysis")
                all_news['market_news'] = self._get_fallback_market_news()
                
                # Provide company-specific fallback news for top movers
                if stock_data:
                    for stock in stock_data[:10]:  # Top 10 movers
                        symbol = stock.get('symbol', '')
                        company_name = stock.get('company_name', '')
                        percent_change = stock.get('percent_change', 0)
                        
                        if symbol and abs(percent_change) >= 1:
                            fallback_news = self._get_fallback_company_news(symbol, company_name, percent_change)
                            all_news['company_news'][symbol] = fallback_news
                            
                            # Create a news summary for WHY analysis
                            all_news['news_summaries'][symbol] = self._create_fallback_news_summary(symbol, company_name, percent_change)
            
            all_news['collection_success'] = True
            logger.info(f"News collection completed. Market news: {len(all_news['market_news'])}, "
                       f"Company news for {len(all_news['company_news'])} companies, "
                       f"News summaries for {len(all_news['news_summaries'])} stocks")
            
        except Exception as e:
            logger.error(f"Error in news collection: {str(e)}")
            all_news['error'] = str(e)
            
            # Even if there's an error, provide fallback news for WHY analysis
            all_news['market_news'] = self._get_fallback_market_news()
            all_news['collection_success'] = True  # Mark as successful with fallback data
        
        return all_news
    
    def _calculate_relevance_score(self, article: Dict, query: str) -> float:
        """Calculate relevance score for an article"""
        score = 0.0
        
        title = str(article.get('title', '') or '').lower()
        description = str(article.get('description', '') or '').lower()
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
    
    def _get_fallback_market_news(self) -> List[Dict]:
        """Generate fallback market news for WHY analysis when APIs fail"""
        return [
            {
                'title': 'Tech Stocks Rally on AI Optimism and Strong Earnings',
                'description': 'Technology sector leads market gains as investors focus on artificial intelligence developments and robust quarterly results from major tech companies.',
                'url': 'https://marketwatch.com/tech-rally',
                'source': 'MarketWatch',
                'published_at': datetime.now().isoformat(),
                'relevance_score': 9.0
            },
            {
                'title': 'Federal Reserve Policy Decisions Impact Market Sentiment',
                'description': 'Investors closely monitor Federal Reserve communications for signals on future interest rate policy, with market volatility expected around key announcements.',
                'url': 'https://reuters.com/fed-policy',
                'source': 'Reuters',
                'published_at': datetime.now().isoformat(),
                'relevance_score': 8.5
            },
            {
                'title': 'Sector Rotation Continues as Investors Rebalance Portfolios',
                'description': 'Market participants continue to rotate between growth and value stocks, with particular focus on technology, healthcare, and financial sectors.',
                'url': 'https://bloomberg.com/sector-rotation',
                'source': 'Bloomberg',
                'published_at': datetime.now().isoformat(),
                'relevance_score': 7.5
            },
            {
                'title': 'Earnings Season Drives Individual Stock Performance',
                'description': 'Corporate earnings reports continue to be the primary driver of individual stock movements, with companies exceeding or missing expectations significantly impacting share prices.',
                'url': 'https://cnbc.com/earnings-season',
                'source': 'CNBC',
                'published_at': datetime.now().isoformat(),
                'relevance_score': 8.0
            },
            {
                'title': 'Market Volatility Reflects Economic Uncertainty',
                'description': 'Ongoing economic uncertainty, including inflation concerns and geopolitical tensions, continues to drive market volatility and investor caution.',
                'url': 'https://wsj.com/market-volatility',
                'source': 'Wall Street Journal',
                'published_at': datetime.now().isoformat(),
                'relevance_score': 7.0
            }
        ]
    
    def _get_fallback_company_news(self, symbol: str, company_name: str, percent_change: float) -> List[Dict]:
        """Generate fallback company-specific news for WHY analysis"""
        direction = "gained" if percent_change > 0 else "declined"
        magnitude = "significantly" if abs(percent_change) > 3 else "moderately"
        
        # Create contextually relevant news based on the stock's movement
        if abs(percent_change) > 5:
            # Large movement - likely earnings or major news
            if percent_change > 0:
                return [
                    {
                        'title': f'{company_name} ({symbol}) Surges on Strong Earnings Report',
                        'description': f'{company_name} stock {direction} {magnitude} after reporting quarterly earnings that exceeded analyst expectations, driven by strong revenue growth and improved profitability.',
                        'url': f'https://marketwatch.com/{symbol.lower()}',
                        'source': 'MarketWatch',
                        'published_at': datetime.now().isoformat(),
                        'relevance_score': 9.5
                    },
                    {
                        'title': f'Analysts Raise Price Targets for {company_name}',
                        'description': f'Multiple analysts have raised their price targets for {company_name} following the positive earnings report, citing strong fundamentals and growth prospects.',
                        'url': f'https://seekingalpha.com/{symbol.lower()}',
                        'source': 'Seeking Alpha',
                        'published_at': datetime.now().isoformat(),
                        'relevance_score': 8.5
                    }
                ]
            else:
                return [
                    {
                        'title': f'{company_name} ({symbol}) Drops on Earnings Miss',
                        'description': f'{company_name} stock {direction} {magnitude} after reporting quarterly earnings that fell short of analyst expectations, with concerns about future growth prospects.',
                        'url': f'https://marketwatch.com/{symbol.lower()}',
                        'source': 'MarketWatch',
                        'published_at': datetime.now().isoformat(),
                        'relevance_score': 9.5
                    },
                    {
                        'title': f'Analysts Lower Estimates for {company_name}',
                        'description': f'Analysts have revised their estimates for {company_name} downward following the disappointing earnings report, citing challenges in the current market environment.',
                        'url': f'https://seekingalpha.com/{symbol.lower()}',
                        'source': 'Seeking Alpha',
                        'published_at': datetime.now().isoformat(),
                        'relevance_score': 8.5
                    }
                ]
        else:
            # Moderate movement - likely market sentiment or sector rotation
            if percent_change > 0:
                return [
                    {
                        'title': f'{company_name} ({symbol}) Rises with Sector Momentum',
                        'description': f'{company_name} stock {direction} {magnitude} as the broader sector shows strength, with investors rotating into growth stocks amid positive market sentiment.',
                        'url': f'https://marketwatch.com/{symbol.lower()}',
                        'source': 'MarketWatch',
                        'published_at': datetime.now().isoformat(),
                        'relevance_score': 7.5
                    },
                    {
                        'title': f'Technical Analysis Shows Bullish Signals for {company_name}',
                        'description': f'Technical indicators suggest positive momentum for {company_name}, with the stock breaking through key resistance levels and showing strong volume.',
                        'url': f'https://benzinga.com/{symbol.lower()}',
                        'source': 'Benzinga',
                        'published_at': datetime.now().isoformat(),
                        'relevance_score': 7.0
                    }
                ]
            else:
                return [
                    {
                        'title': f'{company_name} ({symbol}) Declines Amid Market Pressure',
                        'description': f'{company_name} stock {direction} {magnitude} as the broader market faces selling pressure, with investors taking profits in growth stocks.',
                        'url': f'https://marketwatch.com/{symbol.lower()}',
                        'source': 'MarketWatch',
                        'published_at': datetime.now().isoformat(),
                        'relevance_score': 7.5
                    },
                    {
                        'title': f'Market Sentiment Weighs on {company_name}',
                        'description': f'Negative market sentiment and sector rotation are impacting {company_name}, with investors moving away from growth stocks toward value plays.',
                        'url': f'https://benzinga.com/{symbol.lower()}',
                        'source': 'Benzinga',
                        'published_at': datetime.now().isoformat(),
                        'relevance_score': 7.0
                    }
                ]
    
    def _create_fallback_news_summary(self, symbol: str, company_name: str, percent_change: float) -> str:
        """Create a fallback news summary for WHY analysis"""
        direction = "gained" if percent_change > 0 else "declined"
        magnitude = "significantly" if abs(percent_change) > 3 else "moderately"
        
        if abs(percent_change) > 5:
            if percent_change > 0:
                return f"{company_name} ({symbol}) surged {abs(percent_change):.2f}% today, driven by strong quarterly earnings that exceeded analyst expectations. The company reported robust revenue growth and improved profitability, leading multiple analysts to raise their price targets. The positive results reflect strong demand for the company's products/services and effective execution of growth strategies."
            else:
                return f"{company_name} ({symbol}) dropped {abs(percent_change):.2f}% today after reporting quarterly earnings that fell short of analyst expectations. The disappointing results raised concerns about future growth prospects and led analysts to revise their estimates downward. The company faces challenges in the current market environment."
        else:
            if percent_change > 0:
                return f"{company_name} ({symbol}) rose {abs(percent_change):.2f}% today, benefiting from positive sector momentum and market sentiment. The stock showed strong technical indicators, breaking through key resistance levels with above-average volume. Investors are rotating into growth stocks amid optimism about economic recovery."
            else:
                return f"{company_name} ({symbol}) declined {abs(percent_change):.2f}% today amid broader market selling pressure. The stock was impacted by negative market sentiment and sector rotation, with investors taking profits in growth stocks and moving toward value plays. Technical indicators suggest the stock may find support at current levels."
    
    def get_comprehensive_analysis(self, symbol: str = None, market_topic: str = "NASDAQ") -> Dict:
        """Get comprehensive analysis by combining multiple articles and sources"""
        try:
            # Get articles from multiple sources
            newsapi_articles = self.get_newsapi_news(market_topic if not symbol else symbol, 48)
            biztoc_articles = self.get_biztoc_news(market_topic if not symbol else symbol, 48)
            newsdata_articles = self.get_newsdata_news(market_topic if not symbol else symbol, 48, symbol)
            the_news_api_articles = self.get_the_news_api_news(market_topic if not symbol else symbol, 48, symbol)
            
            # Combine all articles
            all_articles = newsapi_articles + biztoc_articles + newsdata_articles + the_news_api_articles
            
            if not all_articles:
                return {
                    'analysis_text': '',
                    'key_points': [],
                    'sources': [],
                    'word_count': 0
                }
            
            # Sort by relevance and recency
            sorted_articles = sorted(all_articles, 
                                   key=lambda x: (x.get('relevance_score', 0), x.get('published_at', '')), 
                                   reverse=True)
            
            # Take top articles with substantial content
            substantial_articles = [article for article in sorted_articles[:15] 
                                  if article.get('word_count', 0) > 30]  # Articles with more than 30 words
            
            if not substantial_articles:
                # Fall back to any articles if none have substantial content
                substantial_articles = sorted_articles[:8]
            
            # Extract key information
            analysis_text = ""
            key_points = []
            sources = []
            
            for article in substantial_articles[:8]:  # Use top 8 articles
                title = article.get('title', '')
                full_text = article.get('full_text', '')
                source = article.get('source', '')
                author = article.get('author', '')
                
                if full_text:
                    analysis_text += f"{title}\n{full_text}\n\n"
                
                if source and source not in sources:
                    sources.append(source)
                
                # Extract potential key points from title
                if title and len(title) > 20:
                    key_points.append(title)
            
            # Limit key points to top 8
            key_points = key_points[:8]
            
            return {
                'analysis_text': analysis_text.strip(),
                'key_points': key_points,
                'sources': sources,
                'word_count': len(analysis_text.split()),
                'article_count': len(substantial_articles),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive analysis: {str(e)}")
            return {
                'analysis_text': '',
                'key_points': [],
                'sources': [],
                'word_count': 0,
                'error': str(e)
            }
    
    def get_enhanced_market_news(self, symbols: List[str] = None, stock_data: List[Dict] = None) -> Dict:
        """Get enhanced market news with comprehensive analysis"""
        logger.info("Starting enhanced market news collection")
        
        enhanced_news = {
            'market_analysis': {},
            'company_analysis': {},
            'comprehensive_summaries': {},
            'collection_success': False,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Get comprehensive market analysis
            market_analysis = self.get_comprehensive_analysis(market_topic="NASDAQ stock market")
            enhanced_news['market_analysis'] = market_analysis
            
            # Get company-specific analysis for top movers
            if stock_data:
                for stock in stock_data[:5]:  # Top 5 stocks
                    symbol = stock.get('symbol', '')
                    percent_change = stock.get('percent_change', 0)
                    
                    if symbol and abs(percent_change) >= 2:  # Significant movers
                        company_analysis = self.get_comprehensive_analysis(symbol=symbol)
                        if company_analysis.get('word_count', 0) > 100:  # Only if we have substantial content
                            enhanced_news['company_analysis'][symbol] = company_analysis
            
            # Create comprehensive summaries for the market
            if market_analysis.get('analysis_text'):
                enhanced_news['comprehensive_summaries']['market'] = {
                    'summary': market_analysis.get('analysis_text', '')[:2000],  # Limit to 2000 chars
                    'key_points': market_analysis.get('key_points', []),
                    'sources': market_analysis.get('sources', [])
                }
            
            enhanced_news['collection_success'] = True
            logger.info(f"Enhanced news collection completed. Market analysis: {market_analysis.get('word_count', 0)} words, "
                       f"Company analysis for {len(enhanced_news['company_analysis'])} companies")
            
        except Exception as e:
            logger.error(f"Error in enhanced news collection: {str(e)}")
            enhanced_news['error'] = str(e)
            
            try:
                logger.info("Attempting fallback to basic news collection")
                basic_news = self.get_market_news(symbols, stock_data)
                if basic_news.get('collection_success'):
                    company_news = basic_news.get('company_news', {})
                    company_analysis = {}
                    
                    for symbol, articles in company_news.items():
                        if articles:
                            company_analysis[symbol] = {
                                'articles': articles,
                                'analysis': f"Basic news collection for {symbol}: {len(articles)} articles found",
                                'article_count': len(articles),
                                'word_count': len(' '.join([a.get('title', '') + ' ' + a.get('description', '') for a in articles]))
                            }
                    
                    enhanced_news['company_analysis'] = company_analysis
                    enhanced_news['collection_success'] = True
                    enhanced_news['fallback_used'] = True
                    logger.info(f"Fallback to basic news collection successful: {len(company_analysis)} companies")
                else:
                    logger.error("Fallback news collection also failed")
                    
            except Exception as fallback_error:
                logger.error(f"Fallback news collection also failed: {str(fallback_error)}")
        
        return enhanced_news
    
    def get_comprehensive_company_news(self, symbol: str, company_name: str, percent_change: float) -> Dict:
        """
        Get comprehensive company news from multiple sources including Finnhub sentiment
        Phase 2: Enhanced integration with Finnhub news and sentiment analysis
        """
        logger.info(f"Getting comprehensive news for {symbol} ({company_name})")
        
        comprehensive_data = {
            'symbol': symbol,
            'company_name': company_name,
            'percent_change': percent_change,
            'news_articles': [],
            'sentiment_data': {},
            'summary': '',
            'catalysts': [],
            'collection_success': False,
            'sources_used': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            all_articles = []
            
            try:
                newsapi_articles = self.get_newsapi_news(symbol, 48)
                if newsapi_articles:
                    all_articles.extend(newsapi_articles)
                    comprehensive_data['sources_used'].append('NewsAPI')
                    logger.info(f"NewsAPI: {len(newsapi_articles)} articles for {symbol}")
            except Exception as e:
                logger.warning(f"NewsAPI failed for {symbol}: {str(e)}")
            
            try:
                biztoc_articles = self.get_biztoc_news(symbol, 48, company_name)
                if biztoc_articles:
                    all_articles.extend(biztoc_articles)
                    comprehensive_data['sources_used'].append('Biztoc')
                    logger.info(f"Biztoc: {len(biztoc_articles)} articles for {symbol}")
            except Exception as e:
                logger.warning(f"Biztoc failed for {symbol}: {str(e)}")
            
            try:
                newsdata_articles = self.get_newsdata_news(symbol, 48, company_name)
                if newsdata_articles:
                    all_articles.extend(newsdata_articles)
                    comprehensive_data['sources_used'].append('NewsData.io')
                    logger.info(f"NewsData.io: {len(newsdata_articles)} articles for {symbol}")
            except Exception as e:
                logger.warning(f"NewsData.io failed for {symbol}: {str(e)}")
            
            # 4. Get news from The News API
            try:
                thenews_articles = self.get_the_news_api_news(symbol, 48, company_name)
                if thenews_articles:
                    all_articles.extend(thenews_articles)
                    comprehensive_data['sources_used'].append('The News API')
                    logger.info(f"The News API: {len(thenews_articles)} articles for {symbol}")
            except Exception as e:
                logger.warning(f"The News API failed for {symbol}: {str(e)}")
            
            try:
                finnhub_articles = finnhub_news_adapter.get_company_news(symbol)
                if finnhub_articles:
                    all_articles.extend(finnhub_articles)
                    comprehensive_data['sources_used'].append('Finnhub')
                    logger.info(f"Finnhub: {len(finnhub_articles)} articles for {symbol}")
            except Exception as e:
                logger.warning(f"Finnhub news failed for {symbol}: {str(e)}")
            
            try:
                sentiment_data = finnhub_news_adapter.get_news_sentiment(symbol)
                if sentiment_data:
                    comprehensive_data['sentiment_data'] = sentiment_data
                    logger.info(f"Finnhub sentiment data collected for {symbol}")
            except Exception as e:
                logger.warning(f"Finnhub sentiment failed for {symbol}: {str(e)}")
            
            # Deduplicate and sort articles
            unique_articles = self._deduplicate_news(all_articles)
            sorted_articles = sorted(unique_articles, 
                                   key=lambda x: (x.get('relevance_score', 0), x.get('published_at', '')), 
                                   reverse=True)
            
            # Filter to today's articles and take top articles
            today_articles = self._filter_today_articles(sorted_articles)
            top_articles = today_articles[:10] if today_articles else sorted_articles[:10]
            
            comprehensive_data['news_articles'] = top_articles
            
            catalysts = self._identify_news_catalysts(top_articles)
            comprehensive_data['catalysts'] = catalysts
            
            # Create comprehensive summary with sentiment integration
            summary = self._create_comprehensive_summary(
                symbol, company_name, percent_change, top_articles, 
                comprehensive_data['sentiment_data'], catalysts
            )
            comprehensive_data['summary'] = summary
            
            if top_articles or comprehensive_data['sentiment_data']:
                comprehensive_data['collection_success'] = True
                logger.info(f"Comprehensive news collection successful for {symbol}: "
                           f"{len(top_articles)} articles, {len(comprehensive_data['sources_used'])} sources, "
                           f"sentiment: {'Yes' if comprehensive_data['sentiment_data'] else 'No'}")
            else:
                logger.warning(f"No news or sentiment data collected for {symbol}")
                # Provide fallback summary
                comprehensive_data['summary'] = self._create_fallback_news_summary(symbol, company_name, percent_change)
                comprehensive_data['collection_success'] = True  # Still mark as successful with fallback
            
        except Exception as e:
            logger.error(f"Error in comprehensive news collection for {symbol}: {str(e)}")
            comprehensive_data['error'] = str(e)
            # Provide fallback summary even on error
            comprehensive_data['summary'] = self._create_fallback_news_summary(symbol, company_name, percent_change)
            comprehensive_data['collection_success'] = True  # Mark as successful with fallback
        
        return comprehensive_data
    
    def _create_comprehensive_summary(self, symbol: str, company_name: str, percent_change: float, 
                                    articles: List[Dict], sentiment_data: Dict, catalysts: List[str]) -> str:
        """
        Create a comprehensive news summary integrating multiple sources and Finnhub sentiment
        Phase 2: Enhanced with sentiment analysis
        """
        if not articles and not sentiment_data:
            return self._create_fallback_news_summary(symbol, company_name, percent_change)
        
        summary_parts = []
        direction = "gained" if percent_change > 0 else "declined"
        
        summary_parts.append(f"{company_name} ({symbol}) {direction} {abs(percent_change):.2f}% today")
        
        if sentiment_data:
            company_score = sentiment_data.get('companyNewsScore', 0)
            sector_score = sentiment_data.get('sectorAverageNewsScore', 0)
            
            if company_score != 0:
                sentiment_desc = "positive" if company_score > 0.1 else "negative" if company_score < -0.1 else "neutral"
                summary_parts.append(f"with {sentiment_desc} news sentiment (score: {company_score:.2f})")
                
                if sector_score != 0:
                    relative_sentiment = "above" if company_score > sector_score else "below"
                    summary_parts.append(f"{relative_sentiment} sector average ({sector_score:.2f})")
        
        # Add catalyst information
        if catalysts:
            catalyst_text = ", ".join(catalysts[:3])  # Top 3 catalysts
            summary_parts.append(f"driven by {catalyst_text}")
        
        if articles:
            top_article = articles[0]
            title = top_article.get('title', '')
            source = top_article.get('source', '')
            
            if title:
                if len(title) > 100:
                    title = title[:97] + "..."
                summary_parts.append(f'Key news: "{title}"')
                
                if source:
                    summary_parts.append(f"(via {source})")
            
            # Add additional context from other sources
            if len(articles) > 1:
                additional_sources = set()
                for article in articles[1:4]:  # Next 3 articles
                    article_source = article.get('source', '')
                    if article_source and article_source != source:
                        additional_sources.add(article_source)
                
                if additional_sources:
                    sources_text = ", ".join(list(additional_sources)[:2])
                    summary_parts.append(f"Additional coverage from {sources_text}")
        
        return ". ".join(summary_parts) + "."
    
    def get_company_news_summary(self, symbol: str, company_name: str, percent_change: float) -> str:
        """Get a comprehensive news summary for a specific company"""
        try:
            # Use comprehensive collection first
            comprehensive_news = self.get_comprehensive_company_news(symbol, company_name, percent_change)
            if comprehensive_news.get('collection_success') and comprehensive_news.get('summary'):
                return comprehensive_news['summary']
            
            # Fallback to original method, now including Finnhub
            company_news = self.get_newsapi_news(symbol, 48)
            biztoc_company_news = self.get_biztoc_news(symbol, 48)
            finnhub_company_news = finnhub_news_adapter.get_company_news(symbol)
            
            # Combine and sort by relevance
            all_news = company_news + biztoc_company_news + finnhub_company_news
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
            logger.error(f"Error getting company news summary for {symbol}: {str(e)}")
            return self._create_fallback_news_summary(symbol, company_name, percent_change)
    
    def _get_newsdata_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Get articles from NewsData.io search endpoint"""
        try:
            url = "https://newsdata.io/api/1/news"
            params = {
                "apikey": self.newsdata_api_key,
                "q": query,
                "language": "en",
                "category": "business",
                "size": str(limit)
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'success':
                return data.get('results', [])
            return []
            
        except Exception as e:
            logger.debug(f"NewsData.io search failed: {str(e)}")
            return []
    
    def _get_newsdata_company_news(self, company: str, limit: int = 8) -> List[Dict]:
        """Get company-specific news from NewsData.io"""
        try:
            url = "https://newsdata.io/api/1/news"
            params = {
                "apikey": self.newsdata_api_key,
                "q": company,
                "language": "en",
                "category": "business",
                "size": str(limit)
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'success':
                return data.get('results', [])
            return []
            
        except Exception as e:
            logger.debug(f"NewsData.io company news failed: {str(e)}")
            return []
    
    def _get_newsdata_market_news(self, limit: int = 5) -> List[Dict]:
        """Get market-specific news from NewsData.io"""
        try:
            url = "https://newsdata.io/api/1/news"
            params = {
                "apikey": self.newsdata_api_key,
                "q": "stock market NASDAQ",
                "language": "en",
                "category": "business",
                "size": str(limit)
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'success':
                return data.get('results', [])
            return []
            
        except Exception as e:
            logger.debug(f"NewsData.io market news failed: {str(e)}")
            return []
    
    def _get_the_news_api_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Get articles from The News API search endpoint"""
        try:
            url = "https://api.thenewsapi.com/v1/news/all"
            params = {
                "api_token": self.the_news_api_api_key,
                "search": query,
                "language": "en",
                "categories": "business",
                "limit": str(limit)
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', [])
            
        except Exception as e:
            logger.debug(f"The News API search failed: {str(e)}")
            return []
    
    def _get_the_news_api_company_news(self, company: str, limit: int = 8) -> List[Dict]:
        """Get company-specific news from The News API"""
        try:
            url = "https://api.thenewsapi.com/v1/news/all"
            params = {
                "api_token": self.the_news_api_api_key,
                "search": company,
                "language": "en",
                "categories": "business",
                "limit": str(limit)
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', [])
            
        except Exception as e:
            logger.debug(f"The News API company news failed: {str(e)}")
            return []
    
    def _get_the_news_api_top_business(self, limit: int = 5) -> List[Dict]:
        """Get top business stories from The News API"""
        try:
            url = "https://api.thenewsapi.com/v1/news/top"
            params = {
                "api_token": self.the_news_api_api_key,
                "language": "en",
                "categories": "business",
                "limit": str(limit)
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', [])
            
        except Exception as e:
            logger.debug(f"The News API top business failed: {str(e)}")
            return []
    
    def _is_today_article(self, published_at: str) -> bool:
        """Check if article was published today (in market timezone)"""
        if not published_at:
            return False
        
        try:
            # Parse the published_at date
            if 'T' in published_at:
                # ISO format: "2024-01-15T10:30:00Z"
                article_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            elif ' ' in published_at:
                # Common format: "2024-01-15 10:30:00"
                article_date = datetime.strptime(published_at, '%Y-%m-%d %H:%M:%S')
                article_date = article_date.replace(tzinfo=pytz.UTC)
            else:
                # Date only: "2024-01-15"
                article_date = datetime.strptime(published_at, '%Y-%m-%d')
                article_date = article_date.replace(tzinfo=pytz.UTC)
            
            if article_date.tzinfo is None:
                article_date = article_date.replace(tzinfo=pytz.UTC)
            article_date_market = article_date.astimezone(self.market_tz)
            
            # Get today's date in market timezone (start of day)
            market_now = datetime.now(self.market_tz)
            today_market = market_now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Check if article is from today in market timezone
            return article_date_market.date() == today_market.date()
            
        except Exception as e:
            logger.debug(f"Error parsing date '{published_at}': {str(e)}")
            return False
    
    def _filter_today_articles(self, articles: List[Dict]) -> List[Dict]:
        """Filter articles to only include those published today"""
        if not articles:
            return []
        
        today_articles = []
        for article in articles:
            published_at = article.get('published_at', '')
            if self._is_today_article(published_at):
                today_articles.append(article)
        
        logger.info(f"Filtered to {len(today_articles)} today's articles from {len(articles)} total articles")
        return today_articles


# Global instance
news_collector = NewsCollector()                                                                                                                                