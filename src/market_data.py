"""
NASDAQ-100 Market Data Collector
Fetches daily performance data and relevant news for top movers
"""

import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path
import time
import warnings
from tenacity import retry, stop_after_attempt, wait_exponential
import yfinance as yf

# Suppress warnings
warnings.filterwarnings('ignore', category=FutureWarning)

# Configure API keys
FMP_API_KEY = os.getenv('FMP_API_KEY')
if not FMP_API_KEY:
    raise ValueError("FMP_API_KEY environment variable not set")

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

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_fmp_data(endpoint, params=None):
    """Fetch data from FMP API with retry logic"""
    base_url = "https://financialmodelingprep.com/api/v3"
    url = f"{base_url}/{endpoint}"
    
    params = params or {}
    params['apikey'] = FMP_API_KEY
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def get_nasdaq100_tickers():
    """Get NASDAQ-100 constituents from FMP API with fallback to Wikipedia"""
    try:
        logging.info("Fetching NASDAQ-100 constituents from FMP...")
        indices = fetch_fmp_data("nasdaq_constituent")
        tickers = [stock['symbol'] for stock in indices]
        logging.info(f"Successfully retrieved {len(tickers)} tickers from FMP")
        return tickers
        
    except Exception as e:
        logging.warning(f"Error fetching from FMP: {str(e)}. Using fallback method.")
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

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_stock_quote(ticker):
    """Get current stock quote from FMP"""
    try:
        quote = fetch_fmp_data(f"quote/{ticker}")
        if quote and len(quote) > 0:
            return quote[0]
        raise ValueError(f"No quote data returned for {ticker}")
    except Exception as e:
        logging.error(f"Error fetching quote for {ticker}: {str(e)}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_stock_profile(ticker):
    """Get company profile from FMP"""
    try:
        profile = fetch_fmp_data(f"profile/{ticker}")
        if profile and len(profile) > 0:
            return profile[0]
        raise ValueError(f"No profile data returned for {ticker}")
    except Exception as e:
        logging.error(f"Error fetching profile for {ticker}: {str(e)}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_stock_news(ticker):
    """Get stock news from FMP"""
    try:
        # Get company news
        news = fetch_fmp_data(f"stock_news", {"tickers": ticker, "limit": 5})
        if not news:
            return "No recent news found"
        
        # Format news items
        formatted_news = []
        for item in news[:2]:  # Take top 2 news items
            title = item.get('title', '')
            source = item.get('site', 'Unknown Source')
            formatted_news.append(f"{title} ({source})")
        
        return "; ".join(formatted_news)
    except Exception as e:
        logging.error(f"Error fetching news for {ticker}: {str(e)}")
        return "Error fetching news"

def calculate_technical_indicators(ticker):
    """Calculate technical indicators using FMP data"""
    try:
        # Get technical indicators from FMP
        indicators = fetch_fmp_data(f"technical_indicators/daily/{ticker}", {"period": 14})
        if not indicators:
            return {"rsi": None, "macd": None}
            
        latest = indicators[0] if indicators else {}
        return {
            "rsi": round(float(latest.get('rsi', 0)), 2),
            "macd": round(float(latest.get('macd', 0)), 2)
        }
    except Exception as e:
        logging.error(f"Error calculating technical indicators for {ticker}: {str(e)}")
        return {"rsi": None, "macd": None}

def get_daily_performance(tickers):
    """Get comprehensive daily performance data using FMP"""
    performance_data = []
    successful_tickers = 0
    
    logging.info("Starting to fetch daily performance data...")
    collection_timestamp = datetime.now()
    
    for ticker in tickers:
        try:
            # Add delay between requests
            time.sleep(0.5)
            
            # Get quote data
            quote = get_stock_quote(ticker)
            if not quote:
                continue
                
            # Get company profile
            profile = get_stock_profile(ticker)
            if not profile:
                continue
            
            # Calculate changes
            price = quote.get('price', 0)
            change = quote.get('change', 0)
            change_percent = quote.get('changesPercentage', 0)
            
            # Get technical indicators
            tech_indicators = calculate_technical_indicators(ticker)
            
            # Get news for significant movers (>2% movement)
            news_summary = "No significant move" if abs(change_percent) <= 2 else get_stock_news(ticker)
            
            performance_data.append({
                'ticker': ticker,
                'company_name': profile.get('companyName', ticker),
                'close': round(price, 2),
                'dollar_change': round(change, 2),
                'percent_change': round(change_percent, 2),
                'volume': quote.get('volume', 0),
                'avg_volume': quote.get('avgVolume', 0),
                'volume_ratio': round(quote.get('volume', 0) / quote.get('avgVolume', 1), 2) if quote.get('avgVolume', 0) > 0 else None,
                'collection_timestamp': collection_timestamp,
                'market_cap': profile.get('mktCap', 0),
                'sector': profile.get('sector', ''),
                'industry': profile.get('industry', ''),
                'rsi': tech_indicators['rsi'],
                'macd': tech_indicators['macd'],
                'recent_news': news_summary
            })
            
            successful_tickers += 1
            logging.info(f"Successfully processed {ticker}")
                
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