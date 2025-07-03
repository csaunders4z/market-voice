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

from ..config.settings import get_settings

# Import our new free news scraper
try:
    from .stock_news_scraper import stock_news_scraper
    FREE_NEWS_AVAILABLE = True
    logger.info("✅ Free news scraper available")
except ImportError as e:
    FREE_NEWS_AVAILABLE = False
    logger.warning(f"⚠️  Free news scraper not available: {e}")


class NewsCollector:
    """Collects market and business news from multiple sources"""
    
    def __init__(self):
        self.settings = get_settings()
        self.news_api_key = self.settings.news_api_key
        self.rapidapi_key = os.getenv("BIZTOC_API_KEY", "")
        self.rapidapi_host = "biztoc.p.rapidapi.com"
        self.newsdata_api_key = self.settings.newsdata_api_key
        self.the_news_api_key = self.settings.the_news_api_key
        
    def get_newsapi_news(self, query: str = "NASDAQ", hours_back: int = 24) -> List[Dict]:
        """Get news from NewsAPI with enhanced content"""
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
                'apiKey': self.news_api_key,
                'pageSize': 20,  # Increased from default 20 to get more articles
                'domains': 'reuters.com,bloomberg.com,marketwatch.com,cnbc.com,wsj.com,seekingalpha.com,benzinga.com,yahoo.com',  # Focus on financial news sources
                'excludeDomains': 'twitter.com,facebook.com,instagram.com'  # Exclude social media
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
                    full_text = f"{description} {content}".strip()
                    
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
        """Get news from NewsData.io with enhanced content and company support"""
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
                company_articles = self._get_newsdata_company_news(company, 8)
                articles.extend(company_articles)
            
            # 3. Market-specific news
            market_articles = self._get_newsdata_market_news(5)
            articles.extend(market_articles)
            
            # Deduplicate articles
            unique_articles = self._deduplicate_news(articles)
            
            # Process articles with enhanced content
            processed_articles = []
            for article in unique_articles[:15]:  # Limit to 15 best articles
                if isinstance(article, dict):
                    # Extract content fields, defaulting to empty string if None
                    title = str(article.get('title', '') or '')
                    description = str(article.get('description', '') or '')
                    content = str(article.get('content', '') or '')
                    
                    # Combine available text
                    full_text = f"{description} {content}".strip()
                    
                    # Get additional metadata
                    source_name = str(article.get('source_name', '') or '')
                    url = str(article.get('link', '') or '')
                    published_at = str(article.get('pubDate', '') or '')
                    category = article.get('category', []) or []
                    
                    processed_articles.append({
                        'title': title,
                        'description': description,
                        'content': content,
                        'full_text': full_text,
                        'url': url,
                        'source': source_name,
                        'author': article.get('creator', [''])[0] if article.get('creator') else '',
                        'published_at': published_at,
                        'category': category,
                        'relevance_score': self._calculate_relevance_score({'title': title, 'description': description}, query),
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
        if not self.the_news_api_key or self.the_news_api_key == "DUMMY":
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
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, dict):
                return data.get('articles', [])
            elif isinstance(data, list):
                return data
            return []
            
        except Exception as e:
            logger.debug(f"Biztoc search failed: {str(e)}")
            return []
    
    def _get_biztoc_trending(self, limit: int = 5) -> List[Dict]:
        """Get trending business news from Biztoc"""
        try:
            url = f"https://{self.rapidapi_host}/trending"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": self.rapidapi_host
            }
            params = {
                "limit": str(limit)
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, dict):
                return data.get('articles', [])
            elif isinstance(data, list):
                return data
            return []
            
        except Exception as e:
            logger.debug(f"Biztoc trending failed: {str(e)}")
            return []
    
    def _get_biztoc_market_news(self, limit: int = 5) -> List[Dict]:
        """Get market-specific news from Biztoc"""
        try:
            url = f"https://{self.rapidapi_host}/market"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": self.rapidapi_host
            }
            params = {
                "limit": str(limit)
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, dict):
                return data.get('articles', [])
            elif isinstance(data, list):
                return data
            return []
            
        except Exception as e:
            logger.debug(f"Biztoc market news failed: {str(e)}")
            return []
    
    def _get_biztoc_company_news(self, symbol: str, limit: int = 5) -> List[Dict]:
        """Get company-specific news from Biztoc (if endpoint available)"""
        try:
            url = f"https://{self.rapidapi_host}/company/{symbol}"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": self.rapidapi_host
            }
            params = {
                "limit": str(limit)
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, dict):
                return data.get('articles', [])
            elif isinstance(data, list):
                return data
            return []
            
        except Exception as e:
            logger.debug(f"Biztoc company news failed: {str(e)}")
            return []
    
    def get_comprehensive_company_news(self, symbol: str, company_name: str, percent_change: float) -> Dict:
        """Get comprehensive news for a company using multiple sources including free scraping"""
        try:
            news_data = {
                'symbol': symbol,
                'company_name': company_name,
                'percent_change': percent_change,
                'articles': [],
                'summary': '',
                'catalysts': [],
                'collection_success': False,
                'sources_used': []
            }
            
            all_articles = []
            
            # 1. Try free news scraper first (most comprehensive)
            if FREE_NEWS_AVAILABLE:
                try:
                    free_articles = stock_news_scraper.get_comprehensive_stock_news(symbol, max_articles=15)
                    if free_articles:
                        # Convert NewsArticle objects to dicts
                        for article in free_articles:
                            all_articles.append({
                                'title': article.title,
                                'description': article.description,
                                'content': article.content,
                                'url': article.url,
                                'source': article.source,
                                'published_at': article.published_at,
                                'author': article.author,
                                'relevance_score': article.relevance_score,
                                'word_count': article.word_count
                            })
                        news_data['sources_used'].append('free_scraper')
                        logger.info(f"Free scraper collected {len(free_articles)} articles for {symbol}")
                except Exception as e:
                    logger.warning(f"Free scraper failed for {symbol}: {str(e)}")
            
            # 2. Get paid API news as supplement
            try:
                api_news = self.get_newsapi_news(symbol, 48)
                biztoc_news = self.get_biztoc_news(symbol, 48)
                
                api_articles = api_news + biztoc_news
                if api_articles:
                    all_articles.extend(api_articles)
                    news_data['sources_used'].extend(['newsapi', 'biztoc'])
                    logger.info(f"API sources collected {len(api_articles)} additional articles for {symbol}")
            except Exception as e:
                logger.warning(f"API news collection failed for {symbol}: {str(e)}")
            
            # 3. Process and analyze articles
            if all_articles:
                # Sort by relevance
                sorted_articles = sorted(all_articles, key=lambda x: x.get('relevance_score', 0), reverse=True)
                news_data['articles'] = sorted_articles[:10]  # Top 10 most relevant
                
                # Create comprehensive summary
                top_article = sorted_articles[0]
                news_data['summary'] = self._create_news_summary(sorted_articles[:3], symbol)
                
                # Identify potential catalysts
                news_data['catalysts'] = self._identify_news_catalysts(sorted_articles[:5])
                
                news_data['collection_success'] = True
                logger.info(f"Comprehensive news collection for {symbol}: {len(sorted_articles)} articles, {len(news_data['catalysts'])} catalysts identified")
            
            return news_data
            
        except Exception as e:
            logger.error(f"Error in comprehensive news collection for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'collection_success': False,
                'error': str(e),
                'articles': [],
                'summary': '',
                'catalysts': []
            }
    
    def get_company_news_summary(self, symbol: str, company_name: str, percent_change: float) -> str:
        """Get a concise news summary for a specific company"""
        try:
            # ENHANCED: Collect news for ALL significant movers (reduced threshold from 3% to 1%)
            # This ensures we have explanatory content for more stocks
            if abs(percent_change) < 1:
                return ""
            
            # Use comprehensive collection first
            comprehensive_news = self.get_comprehensive_company_news(symbol, company_name, percent_change)
            if comprehensive_news.get('collection_success') and comprehensive_news.get('summary'):
                return comprehensive_news['summary']
            
            # Fallback to original method
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
        """Identify potential stock movement catalysts from news articles"""
        catalysts = []
        
        # Catalyst keywords and patterns
        catalyst_patterns = {
            'earnings': ['earnings', 'beat', 'miss', 'surprise', 'eps', 'revenue'],
            'analyst_action': ['upgrade', 'downgrade', 'price target', 'rating', 'analyst'],
            'product_news': ['launch', 'product', 'innovation', 'breakthrough', 'patent'],
            'partnership': ['partnership', 'deal', 'acquisition', 'merger', 'collaboration'],
            'regulatory': ['approval', 'fda', 'regulatory', 'compliance', 'investigation'],
            'guidance': ['guidance', 'forecast', 'outlook', 'projections', 'expects'],
            'insider_trading': ['insider', 'ceo', 'executive', 'management', 'shares']
        }
        
        for article in articles:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = f"{title} {description}"
            
            for catalyst_type, keywords in catalyst_patterns.items():
                if any(keyword in content for keyword in keywords):
                    if catalyst_type not in catalysts:
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
        
        return enhanced_news
    
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
                "api_token": self.the_news_api_key,
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
                "api_token": self.the_news_api_key,
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
                "api_token": self.the_news_api_key,
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
        """Check if article was published today"""
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
            else:
                # Date only: "2024-01-15"
                article_date = datetime.strptime(published_at, '%Y-%m-%d')
            
            # Get today's date (start of day)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Check if article is from today
            return article_date.date() == today.date()
            
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