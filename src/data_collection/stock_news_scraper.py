"""
Stock News Scraper for Market Voices
Scrapes free financial news sources for stock-specific content
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import List, Dict, Optional
from src.config.settings import get_settings
from datetime import datetime, timedelta
from urllib.parse import quote, urljoin
import logging
logger = logging.getLogger(__name__)
import random
from dataclasses import dataclass
from src.data_collection.news_collector import news_collector

@dataclass
class NewsArticle:
    """Data class for news articles"""
    title: str
    description: str
    content: str
    url: str
    source: str
    published_at: str
    author: str = ""
    relevance_score: float = 0.0
    word_count: int = 0
    catalyst_type: str = ""

class StockNewsScraper:
    """Scrape free financial news sources for stock-specific content"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Rate limiting
        self.request_delay = 1.0  # 1 second between requests
        self.last_request_time = 0
        
        # Free news sources configuration
        self.sources = {
            'yahoo_finance': {
                'url_template': 'https://finance.yahoo.com/quote/{symbol}/news',
                'enabled': False,  # Disabled due to 404 errors
                'priority': 1
            },
            'seeking_alpha': {
                'url_template': 'https://seekingalpha.com/symbol/{symbol}/news',
                'enabled': False,  # Disabled due to 403 errors
                'priority': 2
            },
            'marketwatch': {
                'url_template': 'https://www.marketwatch.com/investing/stock/{symbol}',
                'enabled': False,  # Disabled due to 401 errors
                'priority': 3
            },
            'benzinga': {
                'url_template': 'https://www.benzinga.com/quote/{symbol}',
                'enabled': True,
                'priority': 4
            },
            'finviz': {
                'url_template': 'https://finviz.com/quote.ashx?t={symbol}',
                'enabled': True,
                'priority': 5
            }
        }
    
    def _rate_limit(self):
        """Implement rate limiting to be respectful to websites"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, timeout: int = 10) -> Optional[requests.Response]:
        """Make HTTP request with error handling and rate limiting"""
        try:
            self._rate_limit()
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed for {url}: {str(e)}")
            return None
    
    def scrape_yahoo_finance_news(self, symbol: str) -> List[NewsArticle]:
        """Scrape Yahoo Finance news for specific stock"""
        articles = []
        try:
            url = f"https://finance.yahoo.com/quote/{symbol}/news"
            response = self._make_request(url)
            if not response:
                return articles
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news articles - Yahoo Finance uses specific CSS classes
            news_items = soup.find_all(['li', 'div'], class_=re.compile(r'.*news.*|.*article.*'))
            
            for item in news_items[:10]:  # Limit to top 10 articles
                try:
                    # Extract title
                    title_elem = item.find(['h3', 'h4', 'a'], class_=re.compile(r'.*title.*|.*headline.*'))
                    if not title_elem:
                        title_elem = item.find('a')
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        article_url = title_elem.get('href', '')
                        
                        # Make URL absolute
                        if article_url.startswith('/'):
                            article_url = urljoin('https://finance.yahoo.com', article_url)
                        elif not article_url.startswith('http'):
                            continue
                        
                        # Extract description/summary
                        desc_elem = item.find(['p', 'div'], class_=re.compile(r'.*summary.*|.*description.*'))
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        
                        # Extract timestamp
                        time_elem = item.find(['time', 'span'], class_=re.compile(r'.*time.*|.*date.*'))
                        published_at = time_elem.get_text(strip=True) if time_elem else ""
                        
                        if title and len(title) > 10:  # Valid title
                            article = NewsArticle(
                                title=title,
                                description=description,
                                content=description,  # Use description as content for now
                                url=article_url,
                                source="Yahoo Finance",
                                published_at=published_at,
                                relevance_score=self._calculate_relevance_score(title, description, symbol),
                                word_count=len(f"{title} {description}".split())
                            )
                            articles.append(article)
                            
                except Exception as e:
                    logger.debug(f"Error parsing Yahoo Finance article: {str(e)}")
                    continue
            
            logger.info(f"Scraped {len(articles)} articles from Yahoo Finance for {symbol}")
            
        except Exception as e:
            logger.error(f"Error scraping Yahoo Finance for {symbol}: {str(e)}")
        
        return articles
    
    def scrape_seeking_alpha_articles(self, symbol: str) -> List[NewsArticle]:
        """Scrape Seeking Alpha for detailed analysis"""
        articles = []
        try:
            url = f"https://seekingalpha.com/symbol/{symbol}/news"
            response = self._make_request(url)
            if not response:
                return articles
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article containers
            article_containers = soup.find_all(['article', 'div'], class_=re.compile(r'.*article.*|.*news.*'))
            
            for container in article_containers[:8]:  # Limit to top 8
                try:
                    # Extract title
                    title_elem = container.find(['h2', 'h3', 'h4', 'a'])
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    article_url = title_elem.get('href', '')
                    
                    # Make URL absolute
                    if article_url.startswith('/'):
                        article_url = urljoin('https://seekingalpha.com', article_url)
                    
                    # Extract description
                    desc_elem = container.find(['p', 'div'], class_=re.compile(r'.*summary.*|.*excerpt.*'))
                    description = desc_elem.get_text(strip=True) if desc_elem else ""
                    
                    # Extract author
                    author_elem = container.find(['span', 'div'], class_=re.compile(r'.*author.*|.*by.*'))
                    author = author_elem.get_text(strip=True) if author_elem else ""
                    
                    # Extract timestamp
                    time_elem = container.find(['time', 'span'], class_=re.compile(r'.*time.*|.*date.*'))
                    published_at = time_elem.get_text(strip=True) if time_elem else ""
                    
                    if title and len(title) > 10:
                        article = NewsArticle(
                            title=title,
                            description=description,
                            content=description,
                            url=article_url,
                            source="Seeking Alpha",
                            published_at=published_at,
                            author=author,
                            relevance_score=self._calculate_relevance_score(title, description, symbol),
                            word_count=len(f"{title} {description}".split())
                        )
                        articles.append(article)
                        
                except Exception as e:
                    logger.debug(f"Error parsing Seeking Alpha article: {str(e)}")
                    continue
            
            logger.info(f"Scraped {len(articles)} articles from Seeking Alpha for {symbol}")
            
        except Exception as e:
            logger.error(f"Error scraping Seeking Alpha for {symbol}: {str(e)}")
        
        return articles
    
    def scrape_marketwatch_stories(self, symbol: str) -> List[NewsArticle]:
        """Scrape MarketWatch for recent stories"""
        articles = []
        try:
            url = f"https://www.marketwatch.com/investing/stock/{symbol}"
            response = self._make_request(url)
            if not response:
                return articles
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news sections
            news_sections = soup.find_all(['div', 'section'], class_=re.compile(r'.*news.*|.*article.*'))
            
            for section in news_sections:
                if hasattr(section, 'find_all'):  # Check if it's a valid BeautifulSoup element
                    articles_in_section = section.find_all(['article', 'div'], class_=re.compile(r'.*story.*|.*headline.*'))
                else:
                    continue
                
                for article_elem in articles_in_section[:6]:  # Limit per section
                    try:
                        # Extract title
                        title_elem = article_elem.find(['h2', 'h3', 'h4', 'a'])
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        article_url = title_elem.get('href', '')
                        
                        # Make URL absolute
                        if article_url.startswith('/'):
                            article_url = urljoin('https://www.marketwatch.com', article_url)
                        
                        # Extract description
                        desc_elem = article_elem.find(['p', 'div'], class_=re.compile(r'.*summary.*|.*description.*'))
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        
                        # Extract timestamp
                        time_elem = article_elem.find(['time', 'span'], class_=re.compile(r'.*time.*|.*date.*'))
                        published_at = time_elem.get_text(strip=True) if time_elem else ""
                        
                        if title and len(title) > 10:
                            article = NewsArticle(
                                title=title,
                                description=description,
                                content=description,
                                url=article_url,
                                source="MarketWatch",
                                published_at=published_at,
                                relevance_score=self._calculate_relevance_score(title, description, symbol),
                                word_count=len(f"{title} {description}".split())
                            )
                            articles.append(article)
                            
                    except Exception as e:
                        logger.debug(f"Error parsing MarketWatch article: {str(e)}")
                        continue
            
            logger.info(f"Scraped {len(articles)} articles from MarketWatch for {symbol}")
            
        except Exception as e:
            logger.error(f"Error scraping MarketWatch for {symbol}: {str(e)}")
        
        return articles
    
    def scrape_benzinga_news(self, symbol: str) -> List[NewsArticle]:
        """Scrape Benzinga for news and analysis"""
        articles = []
        try:
            url = f"https://www.benzinga.com/quote/{symbol}"
            response = self._make_request(url)
            if not response:
                return articles
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news articles
            news_items = soup.find_all(['div', 'article'], class_=re.compile(r'.*news.*|.*story.*'))
            
            for item in news_items[:8]:  # Limit to top 8
                try:
                    # Extract title
                    title_elem = item.find(['h2', 'h3', 'h4', 'a'])
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    article_url = title_elem.get('href', '')
                    
                    # Make URL absolute
                    if article_url.startswith('/'):
                        article_url = urljoin('https://www.benzinga.com', article_url)
                    
                    # Extract description
                    desc_elem = item.find(['p', 'div'], class_=re.compile(r'.*summary.*|.*excerpt.*'))
                    description = desc_elem.get_text(strip=True) if desc_elem else ""
                    
                    # Extract timestamp
                    time_elem = item.find(['time', 'span'], class_=re.compile(r'.*time.*|.*date.*'))
                    published_at = time_elem.get_text(strip=True) if time_elem else ""
                    
                    if title and len(title) > 10:
                        article = NewsArticle(
                            title=title,
                            description=description,
                            content=description,
                            url=article_url,
                            source="Benzinga",
                            published_at=published_at,
                            relevance_score=self._calculate_relevance_score(title, description, symbol),
                            word_count=len(f"{title} {description}".split())
                        )
                        articles.append(article)
                        
                except Exception as e:
                    logger.debug(f"Error parsing Benzinga article: {str(e)}")
                    continue
            
            logger.info(f"Scraped {len(articles)} articles from Benzinga for {symbol}")
            
        except Exception as e:
            logger.error(f"Error scraping Benzinga for {symbol}: {str(e)}")
        
        return articles
    
    def scrape_finviz_news(self, symbol: str) -> List[NewsArticle]:
        """Scrape Finviz for news headlines"""
        articles = []
        try:
            url = f"https://finviz.com/quote.ashx?t={symbol}"
            response = self._make_request(url)
            if not response:
                return articles
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news table
            news_table = soup.find('table', class_='fullview-news-outer')
            if not news_table:
                return articles
            
            news_rows = news_table.find_all('tr')
            
            for row in news_rows[:10]:  # Limit to top 10
                try:
                    cells = row.find_all('td')
                    if len(cells) < 2:
                        continue
                    
                    # Extract timestamp
                    time_cell = cells[0]
                    published_at = time_cell.get_text(strip=True)
                    
                    # Extract title and URL
                    news_cell = cells[1]
                    title_elem = news_cell.find('a')
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        article_url = title_elem.get('href', '')
                        
                        # Extract source
                        source_elem = news_cell.find('span')
                        source = f"Finviz ({source_elem.get_text(strip=True)})" if source_elem else "Finviz"
                        
                        if title and len(title) > 10:
                            article = NewsArticle(
                                title=title,
                                description="",  # Finviz usually only has headlines
                                content="",
                                url=article_url,
                                source=source,
                                published_at=published_at,
                                relevance_score=self._calculate_relevance_score(title, "", symbol),
                                word_count=len(title.split())
                            )
                            articles.append(article)
                            
                except Exception as e:
                    logger.debug(f"Error parsing Finviz article: {str(e)}")
                    continue
            
            logger.info(f"Scraped {len(articles)} articles from Finviz for {symbol}")
            
        except Exception as e:
            logger.error(f"Error scraping Finviz for {symbol}: {str(e)}")
        
        return articles
    
    def get_comprehensive_stock_news(self, symbol: str, max_articles: int = 25) -> List[NewsArticle]:
        """Get comprehensive news from all sources for a stock"""
        all_articles = []
        
        logger.info(f"Starting comprehensive news collection for {symbol}")
        
        # Scrape from all enabled sources
        scrapers = [
            ('yahoo_finance', self.scrape_yahoo_finance_news),
            ('seeking_alpha', self.scrape_seeking_alpha_articles),
            ('marketwatch', self.scrape_marketwatch_stories),
            ('benzinga', self.scrape_benzinga_news),
            ('finviz', self.scrape_finviz_news)
        ]
        
        for source_name, scraper_func in scrapers:
            if self.sources[source_name]['enabled']:
                try:
                    articles = scraper_func(symbol)
                    all_articles.extend(articles)
                    logger.info(f"Collected {len(articles)} articles from {source_name}")
                except Exception as e:
                    logger.error(f"Error collecting from {source_name}: {str(e)}")
                
                # Small delay between sources
                time.sleep(0.5)
        
        # Deduplicate and sort by relevance
        unique_articles = self._deduplicate_articles(all_articles)
        sorted_articles = sorted(unique_articles, key=lambda x: x.relevance_score, reverse=True)
        
        # Filter today's articles
        today_articles = self._filter_today_articles(sorted_articles)
        
        # Return top articles
        result = today_articles[:max_articles]
        
        logger.info(f"Comprehensive news collection for {symbol} completed: {len(result)} unique articles")
        return result
    
    def _calculate_relevance_score(self, title: str, description: str, symbol: str) -> float:
        """Calculate relevance score for an article"""
        score = 0.0
        
        title_lower = title.lower()
        desc_lower = description.lower()
        symbol_lower = symbol.lower()
        
        # Symbol mention bonus
        if symbol_lower in title_lower:
            score += 3.0
        if symbol_lower in desc_lower:
            score += 1.5
        
        # Financial keywords
        financial_keywords = [
            'earnings', 'revenue', 'profit', 'loss', 'guidance', 'outlook',
            'analyst', 'upgrade', 'downgrade', 'price target', 'rating',
            'acquisition', 'merger', 'partnership', 'deal', 'contract',
            'product launch', 'approval', 'regulatory', 'fda', 'sec',
            'dividend', 'buyback', 'split', 'ipo', 'spinoff',
            'beat', 'miss', 'surprise', 'forecast', 'estimate'
        ]
        
        for keyword in financial_keywords:
            if keyword in title_lower:
                score += 1.0
            if keyword in desc_lower:
                score += 0.5
        
        # Market catalyst keywords (higher weight)
        catalyst_keywords = [
            'breakthrough', 'innovation', 'breakthrough', 'launch',
            'partnership', 'deal', 'acquisition', 'merger',
            'approval', 'regulatory', 'fda approval',
            'earnings beat', 'revenue growth', 'guidance raise'
        ]
        
        for keyword in catalyst_keywords:
            if keyword in title_lower:
                score += 2.0
            if keyword in desc_lower:
                score += 1.0
        
        # Recency bonus (approximate)
        time_keywords = ['today', 'breaking', 'just', 'now', 'latest']
        for keyword in time_keywords:
            if keyword in title_lower:
                score += 0.5
        
        return score
    
    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles based on title similarity"""
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            # Create a normalized title for comparison
            normalized_title = re.sub(r'[^\w\s]', '', article.title.lower())
            normalized_title = ' '.join(normalized_title.split())
            
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_articles.append(article)
        
        return unique_articles
    
    def _is_today_article(self, published_at: str) -> bool:
        """Check if article was published today"""
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
            elif len(published_at) == 10:
                # Date only: "2024-01-15"
                article_date = datetime.strptime(published_at, '%Y-%m-%d')
            else:
                # Try to parse as relative time (e.g., "2 hours ago", "Today")
                if 'today' in published_at.lower() or 'now' in published_at.lower():
                    return True
                # For other formats, assume it's recent if we can't parse it
                return True
            
            # Get today's date (start of day)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Check if article is from today
            return article_date.date() == today.date()
            
        except Exception as e:
            logger.debug(f"Error parsing date '{published_at}': {str(e)}")
            # If we can't parse the date, assume it's recent
            return True
    
    def _filter_today_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Filter articles to only include those published today"""
        if not articles:
            return []
        
        today_articles = []
        for article in articles:
            if self._is_today_article(article.published_at):
                today_articles.append(article)
        
        logger.info(f"Filtered to {len(today_articles)} today's articles from {len(articles)} total articles")
        return today_articles
    
    def get_news_for_multiple_stocks(self, symbols: List[str], max_articles_per_stock: int = 15) -> Dict[str, List[NewsArticle]]:
        """Get news for multiple stocks efficiently"""
        results = {}
        
        logger.info(f"Starting news collection for {len(symbols)} stocks")
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"Processing {symbol} ({i}/{len(symbols)})")
            
            try:
                articles = self.get_comprehensive_stock_news(symbol, max_articles_per_stock)
                results[symbol] = articles
                
                logger.info(f"Collected {len(articles)} articles for {symbol}")
                
                # Rate limiting between stocks
                if i < len(symbols):  # Don't sleep after the last stock
                    time.sleep(2.0)  # 2 seconds between stocks
                    
            except Exception as e:
                logger.error(f"Error collecting news for {symbol}: {str(e)}")
                results[symbol] = []
        
        total_articles = sum(len(articles) for articles in results.values())
        logger.info(f"News collection completed: {total_articles} total articles for {len(symbols)} stocks")
        
        return results


# Global instance
stock_news_scraper = StockNewsScraper()