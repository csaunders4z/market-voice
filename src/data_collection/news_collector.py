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
            
            logger.info(f"Retrieved {len(processed_articles)} articles from NewsAPI")
            return processed_articles
            
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
            
            logger.info(f"Retrieved {len(processed_articles)} articles from Biztoc")
            return processed_articles
            
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
            
            logger.info(f"Retrieved {len(processed_articles)} articles from NewsData.io")
            return processed_articles
            
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
            
            logger.info(f"Retrieved {len(processed_articles)} articles from The News API")
            return processed_articles
            
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


# Global instance
news_collector = NewsCollector() 