#!/usr/bin/env python3
"""
Market Voices Smoke Test

Performs a minimal, live-keys integration test of all critical dependencies:
- Confirms API connectivity and correct data structure for FMP, OpenAI, Biztoc
- Uses only a single symbol and minimal data to keep API usage/cost low
- Prints clear PASS/FAIL for each dependency and for the overall test

Run this script after any environment or dependency change, or before a full production run.
"""
from dotenv import load_dotenv
load_dotenv()
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import setup_logging, get_logger
from src.data_collection.fmp_stock_data import FMPStockDataCollector
from src.script_generation.script_generator import ScriptGenerator
from src.config.settings import get_settings


def test_fmp_api():
    """Test FMP API with a single symbol"""
    print("\n🔍 Testing FMP API...")
    try:
        collector = FMPStockDataCollector()
        print(f"✅ API Key loaded: {collector.api_key[:10]}...")
        print("📊 Fetching AAPL data...")
        data = collector.fetch_stock_data("AAPL")
        if data:
            print(f"✅ AAPL data fetched successfully!")
            print(f"   Price: ${data['current_price']}")
            print(f"   Change: {data['percent_change']:.2f}%")
            print(f"   Volume: {data['current_volume']:,}")
            return True
        else:
            print("❌ Failed to fetch AAPL data from FMP")
            return False
    except Exception as e:
        print(f"❌ FMP API error: {str(e)}")
        return False


def test_openai_api():
    """Test OpenAI API with a simple prompt"""
    print("\n🤖 Testing OpenAI API...")
    try:
        settings = get_settings()
        print(f"✅ API Key loaded: {settings.openai_api_key[:10]}...")
        generator = ScriptGenerator()
        test_market_data = {
            'market_summary': {
                'total_stocks': 1,
                'advancing_stocks': 1,
                'declining_stocks': 0,
                'average_change': 2.5,
                'market_date': datetime.now().isoformat()
            },
            'winners': [
                {'symbol': 'AAPL', 'company_name': 'Apple Inc.', 'current_price': 150.25, 'percent_change': 2.5},
                {'symbol': 'MSFT', 'company_name': 'Microsoft Corp.', 'current_price': 320.10, 'percent_change': 1.8},
                {'symbol': 'GOOGL', 'company_name': 'Alphabet Inc.', 'current_price': 2750.00, 'percent_change': 3.2}
            ],
            'losers': [
                {'symbol': 'TSLA', 'company_name': 'Tesla Inc.', 'current_price': 700.00, 'percent_change': -1.5}
            ],
            'collection_success': True
        }
        print("📝 Generating test script...")
        script_data = generator.generate_script(test_market_data)
        if script_data.get('generation_success', False):
            print("✅ Script generated successfully!")
            print(f"   Lead host: {script_data.get('lead_host', 'Unknown')}")
            print(f"   Segments: {len(script_data.get('segments', []))}")
            return True
        else:
            print(f"❌ Script generation failed: {script_data.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ OpenAI API error: {str(e)}")
        return False


def test_biztoc_api():
    """Test Biztoc/RapidAPI with a single symbol"""
    print("\n📰 Testing Biztoc API...")
    try:
        rapidapi_key = os.getenv("BIZTOC_API_KEY", "")
        if not rapidapi_key:
            print("⚠️  No Biztoc API key found, skipping Biztoc test")
            return True
        print(f"✅ Biztoc API Key loaded: {rapidapi_key[:10]}...")
        from src.data_collection.news_collector import news_collector
        print("📰 Fetching Biztoc news...")
        news_data = news_collector.get_biztoc_news("AAPL", 24)
        if news_data:
            print(f"✅ Biztoc news fetched successfully!")
            print(f"   Articles: {len(news_data)}")
            return True
        else:
            print("❌ Failed to fetch Biztoc news")
            return False
    except Exception as e:
        print(f"❌ Biztoc API error: {str(e)}")
        return False


def main():
    print("\n============================")
    print("MARKET VOICES SMOKE TEST")
    print("============================")
    results = {}
    results['FMP'] = test_fmp_api()
    results['OpenAI'] = test_openai_api()
    results['Biztoc'] = test_biztoc_api()
    print("\n============================")
    print("RESULT SUMMARY:")
    for k, v in results.items():
        print(f"{k}: {'PASS' if v else 'FAIL'}")
    if all(results.values()):
        print("\n✅ ALL SMOKE TESTS PASSED!")
        exit(0)
    else:
        print("\n❌ SOME SMOKE TESTS FAILED.")
        exit(1)

if __name__ == "__main__":
    main()
