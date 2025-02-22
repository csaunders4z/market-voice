"""
NASDAQ-100 Market Data Collector
Fetches daily performance data and relevant news for top movers
"""

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import time
import warnings

# Suppress the yfinance FutureWarning
warnings.filterwarnings('ignore', category=FutureWarning)

def setup_logging():
    """Configure logging to both file and console"""
    Path('logs').mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/market_data_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_nasdaq100_tickers():
    """Get NASDAQ-100 constituents with fallback options."""
    try:
        logging.info("Fetching NASDAQ-100 constituents from Wikipedia...")
        tables = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100')
        
        for i, table in enumerate(tables):
            columns = table.columns.tolist()
            possible_ticker_columns = ['Ticker', 'Symbol', 'Ticker symbol']
            
            for col in possible_ticker_columns:
                if col in columns:
                    tickers = table[col].tolist()
                    logging.info(f"Successfully retrieved {len(tickers)} tickers from table {i}")
                    return [ticker.strip() for ticker in tickers if isinstance(ticker, str)]
        
        raise ValueError("Could not find ticker column in Wikipedia tables")
        
    except Exception as e:
        logging.warning(f"Error fetching from Wikipedia: {str(e)}. Using fallback ticker list.")
        fallback_tickers = [
            'AAPL', 'MSFT', 'AMZN', 'NVDA', 'META', 'GOOGL', 'GOOG', 'TSLA', 'AMD', 'ADBE'
        ]
        logging.info(f"Using fallback list of {len(fallback_tickers)} major NASDAQ-100 tickers")
        return fallback_tickers

def calculate_technical_indicators(hist_data):
    """Calculate technical indicators using pandas-ta with improved error handling"""
    try:
        if len(hist_data) < 30:  # Need enough data for calculations
            return {
                'rsi': None,
                'macd': None,
                'macd_signal': None,
                'bb_upper': None,
                'bb_lower': None,
                'atr': None
            }

        df = hist_data.copy()
        
        # Initialize indicators dictionary
        indicators = {
            'rsi': None,
            'macd': None,
            'macd_signal': None,
            'bb_upper': None,
            'bb_lower': None,
            'atr': None
        }
        
        # Calculate RSI
        try:
            rsi = df.ta.rsi(length=14)
            if not rsi.empty and not pd.isna(rsi.iloc[-1]):
                indicators['rsi'] = round(float(rsi.iloc[-1]), 2)
        except Exception as e:
            logging.debug(f"RSI calculation failed: {str(e)}")

        # Calculate MACD
        try:
            macd = df.ta.macd()
            if not macd.empty:
                if not pd.isna(macd['MACD_12_26_9'].iloc[-1]):
                    indicators['macd'] = round(float(macd['MACD_12_26_9'].iloc[-1]), 2)
                if not pd.isna(macd['MACDs_12_26_9'].iloc[-1]):
                    indicators['macd_signal'] = round(float(macd['MACDs_12_26_9'].iloc[-1]), 2)
        except Exception as e:
            logging.debug(f"MACD calculation failed: {str(e)}")

        # Calculate Bollinger Bands
        try:
            bbands = df.ta.bbands()
            if not bbands.empty:
                if not pd.isna(bbands['BBU_20_2.0'].iloc[-1]):
                    indicators['bb_upper'] = round(float(bbands['BBU_20_2.0'].iloc[-1]), 2)
                if not pd.isna(bbands['BBL_20_2.0'].iloc[-1]):
                    indicators['bb_lower'] = round(float(bbands['BBL_20_2.0'].iloc[-1]), 2)
        except Exception as e:
            logging.debug(f"Bollinger Bands calculation failed: {str(e)}")

        # Calculate ATR
        try:
            atr = df.ta.atr()
            if not atr.empty and not pd.isna(atr.iloc[-1]):
                indicators['atr'] = round(float(atr.iloc[-1]), 2)
        except Exception as e:
            logging.debug(f"ATR calculation failed: {str(e)}")

        return indicators

    except Exception as e:
        logging.error(f"Error in technical indicators calculation: {str(e)}")
        return {
            'rsi': None,
            'macd': None,
            'macd_signal': None,
            'bb_upper': None,
            'bb_lower': None,
            'atr': None
        }

def filter_news_relevance(title, percent_change):
    """
    Filter news items for relevance based on various criteria.
    Returns a relevance score (0-1).
    """
    title_lower = title.lower()
    
    # Keywords that indicate price movement explanation
    positive_keywords = ['beats', 'higher', 'jumps', 'surges', 'raises', 'upgraded']
    negative_keywords = ['misses', 'lower', 'falls', 'drops', 'cuts', 'downgraded']
    neutral_keywords = ['earnings', 'announces', 'reports', 'guidance', 'outlook']
    
    # Skip promotional or generic content
    skip_phrases = [
        'named one of', 'best companies', 'what you need to know',
        'stocks to watch', 'trending stock', 'stocks to buy',
        'press release', 'newswires', 'everything you need'
    ]
    
    # Check for generic or promotional content
    if any(phrase in title_lower for phrase in skip_phrases):
        return 0
        
    # Calculate relevance score
    score = 0
    
    # Match movement direction with news sentiment
    if percent_change > 0 and any(word in title_lower for word in positive_keywords):
        score += 0.3
    elif percent_change < 0 and any(word in title_lower for word in negative_keywords):
        score += 0.3
        
    # Additional score for specific event keywords
    if any(word in title_lower for word in neutral_keywords):
        score += 0.2
        
    return score

def get_stock_news(ticker, percent_change):
    """Get and filter relevant news for a stock"""
    try:
        stock = yf.Ticker(ticker)
        news_list = stock.news
        
        if not news_list:
            return "No recent news found"
            
        # Process news items
        relevant_news = []
        for news in news_list:
            title = news.get('title', '')
            relevance = filter_news_relevance(title, percent_change)
            
            if relevance > 0:
                relevant_news.append({
                    'title': title,
                    'source': news.get('publisher', 'Yahoo Finance'),
                    'relevance': relevance
                })
        
        # Sort by relevance and get top 2
        relevant_news.sort(key=lambda x: x['relevance'], reverse=True)
        top_news = relevant_news[:2]
        
        if not top_news:
            return "No relevant news found"
            
        # Format news items
        return '; '.join(f"{item['title']} ({item['source']})" for item in top_news)
        
    except Exception as e:
        logging.error(f"Error fetching news for {ticker}: {str(e)}")
        return "Error fetching news"

def get_daily_performance(tickers):
    """Get comprehensive daily performance data."""
    performance_data = []
    successful_tickers = 0
    
    logging.info("Starting to fetch daily performance data...")
    collection_timestamp = datetime.now()
    
    for ticker in tickers:
        try:
            # Get stock data
            stock = yf.Ticker(ticker)
            hist = stock.history(period='30d')
            
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[-2]
                current_close = hist['Close'].iloc[-1]
                dollar_change = current_close - prev_close
                percent_change = (dollar_change / prev_close) * 100
                
                # Get company info
                company_name = stock.info.get('longName', ticker)
                
                # Get technical indicators
                tech_indicators = calculate_technical_indicators(hist)
                
                # Get news for significant movers (>2% movement)
                news_summary = "No significant move" if abs(percent_change) <= 2 else get_stock_news(ticker, percent_change)
                
                # Calculate volume ratio with error handling
                avg_volume = stock.info.get('averageVolume', 0)
                volume_ratio = round(hist['Volume'].iloc[-1] / avg_volume, 2) if avg_volume else None
                
                performance_data.append({
                    'ticker': ticker,
                    'company_name': company_name,
                    'close': round(current_close, 2),
                    'dollar_change': round(dollar_change, 2),
                    'percent_change': round(percent_change, 2),
                    'volume': hist['Volume'].iloc[-1],
                    'avg_volume': avg_volume,
                    'volume_ratio': volume_ratio,
                    'collection_timestamp': collection_timestamp,
                    'market_cap': stock.info.get('marketCap', 0),
                    'sector': stock.info.get('sector', ''),
                    'industry': stock.info.get('industry', ''),
                    'rsi': tech_indicators['rsi'],
                    'macd': tech_indicators['macd'],
                    'recent_news': news_summary
                })
                
                successful_tickers += 1
                logging.info(f"Successfully processed {ticker}")
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
                
        except Exception as e:
            logging.error(f"Error processing {ticker}: {str(e)}")
            continue
    
    logging.info(f"Completed processing {successful_tickers} out of {len(tickers)} tickers")
    
    if not performance_data:
        raise Exception("No ticker data was successfully processed")
    
    # Create DataFrame and sort by percent change
    df = pd.DataFrame(performance_data)
    df = df.sort_values('percent_change', ascending=False)
    
    return df

def get_top_bottom_movers(df, n=5):
    """Extract top and bottom n movers from the performance DataFrame."""
    top_n = df.head(n)
    bottom_n = df.tail(n)
    
    logging.info(f"Extracted top {n} and bottom {n} movers")
    return top_n, bottom_n

def main():
    # Set up logging
    setup_logging()
    
    try:
        # Create output directory if it doesn't exist
        Path('output').mkdir(exist_ok=True)
        
        # Get current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        logging.info(f"Starting market data collection for {current_date}")
        
        # Get NASDAQ-100 tickers
        tickers = get_nasdaq100_tickers()
        
        # Get performance data
        performance_df = get_daily_performance(tickers)
        
        # Get top and bottom 5 movers
        top_5, bottom_5 = get_top_bottom_movers(performance_df, n=5)
        
        # Save results to CSV files
        output_dir = Path('output')
        top_5.to_csv(output_dir / f'top_movers_{current_date}.csv', index=False)
        bottom_5.to_csv(output_dir / f'bottom_movers_{current_date}.csv', index=False)
        
        logging.info("Successfully completed market data collection")
        return top_5, bottom_5
        
    except Exception as e:
        logging.error(f"Fatal error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        top_movers, bottom_movers = main()
        
        display_columns = [
            'company_name', 'ticker', 'percent_change', 'dollar_change', 
            'volume_ratio', 'rsi', 'sector', 'recent_news'
        ]
        
        print("\nTop 5 Movers:")
        print(top_movers[display_columns].to_string())
        print("\nBottom 5 Movers:")
        print(bottom_movers[display_columns].to_string())
    except Exception as e:
        print(f"Program failed: {str(e)}")
        sys.exit(1)