"""
Free news sources for Market Voices
Collects news from MarketWatch, Reuters, and other free financial sources
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger
import re
from bs4 import BeautifulSoup
import feedparser
import time
import pytz

from src.config.settings import get_settings


class FreeNewsCollector:
    """Collects free news from various financial sources"""
    
    def __init__(self):
        self.settings = get_settings()
        self.market_tz = pytz.timezone('US/Eastern')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_marketwatch_news(self, query: str = "NASDAQ", limit: int = 10) -> List[Dict]:
        """Get news from MarketWatch"""
        try:
            # MarketWatch search URL
            search_url = f"https://www.marketwatch.com/search?q={query}&tab=All"
            
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Find article elements
            article_elements = soup.find_all('div', class_='article__content')
            
            for element in article_elements[:limit]:
                try:
                    # Extract title
                    title_elem = element.find('a', class_='link')
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    
                    # Extract URL
                    url = title_elem.get('href') if title_elem else ''
                    if url and not url.startswith('http'):
                        url = f"https://www.marketwatch.com{url}"
                    
                    # Extract description
                    desc_elem = element.find('p', class_='article__summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ''
                    
                    if title and url:
                        articles.append({
                            'title': title,
                            'description': description,
                            'url': url,
                            'source': 'MarketWatch',
                            'published_at': datetime.now(self.market_tz).isoformat(),
                            'relevance_score': self._calculate_relevance_score({'title': title, 'description': description}, query)
                        })
                        
                except Exception as e:
                    logger.debug(f"Error parsing MarketWatch article: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(articles)} articles from MarketWatch")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching MarketWatch news: {str(e)}")
            return []
    
    def get_reuters_news(self, query: str = "NASDAQ", limit: int = 10) -> List[Dict]:
        """Get news from Reuters"""
        try:
            # Reuters RSS feed for business news
            rss_url = "https://feeds.reuters.com/reuters/businessNews"
            
            feed = feedparser.parse(rss_url)
            articles = []
            
            for entry in feed.entries[:limit]:
                try:
                    title = entry.get('title', '')
                    description = entry.get('summary', '')
                    url = entry.get('link', '')
                    published_at = entry.get('published', '')
                    
                    # Filter for relevant articles
                    if self._is_relevant_article(title, description, query):
                        articles.append({
                            'title': title,
                            'description': description,
                            'url': url,
                            'source': 'Reuters',
                            'published_at': published_at,
                            'relevance_score': self._calculate_relevance_score({'title': title, 'description': description}, query)
                        })
                        
                except Exception as e:
                    logger.debug(f"Error parsing Reuters article: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(articles)} articles from Reuters")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching Reuters news: {str(e)}")
            return []
    
    def get_yahoo_finance_news(self, query: str = "NASDAQ", limit: int = 10) -> List[Dict]:
        """Get news from Yahoo Finance using their API"""
        try:
            import yfinance as yf
            
            # Get news for a broad market ticker
            ticker = yf.Ticker("^IXIC")  # NASDAQ Composite
            news = ticker.news
            
            articles = []
            for item in news[:limit]:
                try:
                    content = item.get('content', {})
                    title = content.get('title', '')
                    summary = content.get('summary', '')
                    description = content.get('description', '')
                    url = content.get('canonicalUrl', '')
                    published_at = content.get('pubDate', '')
                    provider = content.get('provider', 'Yahoo Finance')
                    
                    # Use description if summary is empty
                    full_description = summary if summary else description
                    
                    if title and self._is_relevant_article(title, full_description, query):
                        articles.append({
                            'title': title,
                            'description': full_description,
                            'url': url,
                            'source': provider,
                            'published_at': published_at,
                            'relevance_score': self._calculate_relevance_score({'title': title, 'description': full_description}, query)
                        })
                        
                except Exception as e:
                    logger.debug(f"Error parsing Yahoo Finance article: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(articles)} articles from Yahoo Finance")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance news: {str(e)}")
            return []
    
    def get_company_specific_news(self, symbol: str, limit: int = 5) -> List[Dict]:
        """Get company-specific news from Yahoo Finance"""
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            articles = []
            for item in news[:limit]:
                try:
                    content = item.get('content', {})
                    title = content.get('title', '')
                    summary = content.get('summary', '')
                    description = content.get('description', '')
                    url = content.get('canonicalUrl', '')
                    published_at = content.get('pubDate', '')
                    provider = content.get('provider', 'Yahoo Finance')
                    
                    # Use description if summary is empty
                    full_description = summary if summary else description
                    
                    if title:
                        articles.append({
                            'title': title,
                            'description': full_description,
                            'url': url,
                            'source': provider,
                            'published_at': published_at,
                            'relevance_score': 10.0  # High relevance for company-specific news
                        })
                        
                except Exception as e:
                    logger.debug(f"Error parsing company news: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(articles)} company-specific articles for {symbol}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching company news for {symbol}: {str(e)}")
            return []
    
    def get_reuters_rss_news(self, limit: int = 10) -> List[Dict]:
        """Get business news from Reuters RSS feed"""
        try:
            import feedparser
            rss_url = "https://feeds.reuters.com/reuters/businessNews"
            feed = feedparser.parse(rss_url)
            articles = []
            for entry in feed.entries[:limit]:
                try:
                    title = entry.get('title', '')
                    description = entry.get('summary', '')
                    url = entry.get('link', '')
                    published_at = entry.get('published', '')
                    
                    articles.append({
                        'title': title,
                        'description': description,
                        'url': url,
                        'source': 'Reuters',
                        'published_at': published_at,
                        'relevance_score': self._calculate_relevance_score({'title': title, 'description': description}, 'business')
                    })
                except Exception as e:
                    logger.debug(f"Error parsing Reuters RSS article: {str(e)}")
                    continue
            logger.info(f"Retrieved {len(articles)} articles from Reuters RSS")
            return articles
        except Exception as e:
            logger.error(f"Error fetching Reuters RSS news: {str(e)}")
            return []
    
    def get_marketwatch_rss_news(self, limit: int = 10) -> List[Dict]:
        """Get business news from MarketWatch RSS feed (best effort)"""
        try:
            import feedparser
            rss_url = "https://feeds.marketwatch.com/marketwatch/topstories/"
            feed = feedparser.parse(rss_url)
            articles = []
            for entry in feed.entries[:limit]:
                try:
                    title = entry.get('title', '')
                    description = entry.get('summary', '')
                    url = entry.get('link', '')
                    published_at = entry.get('published', '')
                    
                    articles.append({
                        'title': title,
                        'description': description,
                        'url': url,
                        'source': 'MarketWatch',
                        'published_at': published_at,
                        'relevance_score': self._calculate_relevance_score({'title': title, 'description': description}, 'business')
                    })
                except Exception as e:
                    logger.debug(f"Error parsing MarketWatch RSS article: {str(e)}")
                    continue
            logger.info(f"Retrieved {len(articles)} articles from MarketWatch RSS")
            return articles
        except Exception as e:
            logger.error(f"Error fetching MarketWatch RSS news: {str(e)}")
            return []
    
    def get_comprehensive_free_news(self, query: str = "NASDAQ", limit: int = 15) -> List[Dict]:
        """Get comprehensive news from all free sources"""
        all_articles = []
        
        # Get news from multiple sources
        sources = [
            # ('Yahoo Finance', self.get_yahoo_finance_news),  # Disabled due to parsing errors
            ('Reuters RSS', self.get_reuters_rss_news),
            ('MarketWatch RSS', self.get_marketwatch_rss_news),
        ]
        
        for source_name, source_func in sources:
            try:
                articles = source_func(limit // len(sources))
                all_articles.extend(articles)
                time.sleep(1)  # Be respectful to servers
            except Exception as e:
                logger.warning(f"Failed to get news from {source_name}: {str(e)}")
                continue
        
        # Sort by relevance and recency
        sorted_articles = sorted(all_articles, 
                               key=lambda x: (x.get('relevance_score', 0), x.get('published_at', '')), 
                               reverse=True)
        
        # Remove duplicates
        unique_articles = self._remove_duplicate_articles(sorted_articles)
        
        # Filter today's articles
        today_articles = self._filter_today_articles(unique_articles)
        
        logger.info(f"Retrieved {len(today_articles)} today's articles from free sources")
        return today_articles[:limit]
    
    def _is_relevant_article(self, title: str, description: str, query: str) -> bool:
        """Check if article is relevant to the query"""
        query_terms = query.lower().split()
        text = f"{title} {description}".lower()
        return any(term in text for term in query_terms)
    
    def _calculate_relevance_score(self, article: Dict, query: str) -> float:
        """Calculate relevance score for an article"""
        score = 0.0
        title = str(article.get('title', '')).lower()
        description = str(article.get('description', '')).lower()
        query_terms = query.lower().split()
        
        for term in query_terms:
            if term in title:
                score += 2.0
            if term in description:
                score += 1.0
        
        return score
    
    def _remove_duplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on title similarity"""
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            title = article.get('title', '').lower()
            if title not in seen_titles:
                seen_titles.add(title)
                unique_articles.append(article)
        
        return unique_articles
    
    def _is_today_article(self, published_at: str) -> bool:
        """Check if article was published today (in market timezone)"""
        if not published_at:
            return False
        
        try:
            # Parse the published_at date - handle various formats
            if 'T' in published_at:
                # ISO format: "2024-01-15T10:30:00Z"
                article_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            elif ' ' in published_at and len(published_at) > 10:
                # Common format: "2024-01-15 10:30:00"
                article_date = datetime.strptime(published_at, '%Y-%m-%d %H:%M:%S')
                article_date = article_date.replace(tzinfo=pytz.UTC)
            elif len(published_at) == 10:
                # Date only: "2024-01-15"
                article_date = datetime.strptime(published_at, '%Y-%m-%d')
                article_date = article_date.replace(tzinfo=pytz.UTC)
            elif ',' in published_at and 'GMT' in published_at:
                # RSS format: "Tue, 08 Jul 2025 03:21:00 GMT"
                try:
                    article_date = datetime.strptime(published_at, '%a, %d %b %Y %H:%M:%S GMT')
                    article_date = article_date.replace(tzinfo=pytz.UTC)
                except ValueError:
                    # Try alternative format without day name
                    article_date = datetime.strptime(published_at, '%d %b %Y %H:%M:%S GMT')
                    article_date = article_date.replace(tzinfo=pytz.UTC)
            else:
                # Try to parse as relative time (e.g., "2 hours ago", "Today")
                if 'today' in published_at.lower() or 'now' in published_at.lower():
                    return True
                # For other formats, assume it's recent if we can't parse it
                return True
            
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
            # If we can't parse the date, assume it's recent
            return True
    
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
free_news_collector = FreeNewsCollector()
