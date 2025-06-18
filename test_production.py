#!/usr/bin/env python3
"""
Test Production Mode - Market Voices
Tests production mode with a small subset of symbols and better error handling
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import setup_logging, get_logger
from src.data_collection.fmp_stock_data import FMPStockDataCollector
from src.script_generation.script_generator import ScriptGenerator
from src.content_validation.quality_controls import QualityController
from src.config.settings import get_settings


def test_fmp_api():
    """Test FMP API with a single symbol"""
    print("🔍 Testing FMP API...")
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
        
        # Create a simple test script
        generator = ScriptGenerator()
        
        # Test data
        test_market_data = {
            'market_summary': {
                'total_stocks': 1,
                'advancing_stocks': 1,
                'declining_stocks': 0,
                'average_change': 2.5,
                'market_date': datetime.now().isoformat()
            },
            'winners': [
                {'symbol': 'AAPL', 'company_name': 'Apple Inc.', 'current_price': 150.25, 'percent_change': 2.5}
            ],
            'losers': [],
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
    """Test Biztoc/RapidAPI"""
    print("\n📰 Testing Biztoc API...")
    
    try:
        rapidapi_key = os.getenv("BIZTOC_API_KEY", "")
        if not rapidapi_key:
            print("⚠️  No Biztoc API key found, skipping Biztoc test")
            return True
            
        print(f"✅ Biztoc API Key loaded: {rapidapi_key[:10]}...")
        
        # Test the news collector
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


def test_small_workflow():
    """Test the full workflow with a small subset of symbols using FMP"""
    print("\n🚀 Testing Small Production Workflow (FMP)...")
    try:
        setup_logging()
        logger = get_logger("TestProduction")
        collector = FMPStockDataCollector()
        print(f"📊 Collecting data for {len(collector.symbols)} symbols...")
        all_data = collector.collect_data()
        if all_data:
            print("✅ Market data collected successfully!")
            print(f"   Symbols: {len(all_data)}")
            # Prepare market_data dict for script generator
            market_data = {
                'market_summary': {
                    'total_stocks': len(all_data),
                    'advancing_stocks': sum(1 for d in all_data if d['percent_change'] > 0),
                    'declining_stocks': sum(1 for d in all_data if d['percent_change'] < 0),
                    'average_change': sum(d['percent_change'] for d in all_data) / len(all_data),
                    'market_date': datetime.now().isoformat()
                },
                'winners': sorted(all_data, key=lambda d: d['percent_change'], reverse=True)[:3],
                'losers': sorted(all_data, key=lambda d: d['percent_change'])[:3],
                'collection_success': True
            }
            print("📝 Generating script...")
            generator = ScriptGenerator()
            script_data = generator.generate_script(market_data)
            if script_data.get('generation_success', False):
                print("✅ Script generated successfully!")
                print(f"   Lead host: {script_data.get('lead_host', 'Unknown')}")
                print(f"   Segments: {len(script_data.get('segments', []))}")
                print("🔍 Validating quality...")
                quality_controller = QualityController()
                quality_results = quality_controller.validate_script_quality(script_data)
                print(f"✅ Quality validation completed!")
                print(f"   Score: {quality_results.get('overall_score', 0):.1f}%")
                return True
            else:
                print(f"❌ Script generation failed: {script_data.get('error', 'Unknown error')}")
                return False
        else:
            print("❌ Market data collection failed (FMP)")
            return False
    except Exception as e:
        print(f"❌ Workflow error: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🧪 MARKET VOICES - PRODUCTION TEST")
    print("=" * 50)
    fmp_ok = test_fmp_api()
    openai_ok = test_openai_api()
    biztoc_ok = test_biztoc_api()
    print("\n" + "=" * 50)
    print("📋 API Test Results:")
    print(f"   FMP: {'✅' if fmp_ok else '❌'}")
    print(f"   OpenAI: {'✅' if openai_ok else '❌'}")
    print(f"   Biztoc: {'✅' if biztoc_ok else '❌'}")
    if fmp_ok and openai_ok:
        print("\n" + "=" * 50)
        workflow_ok = test_small_workflow()
        print(f"\n🎯 Full Workflow: {'✅ SUCCESS' if workflow_ok else '❌ FAILED'}")
    else:
        print("\n⚠️  Skipping full workflow test due to API failures")
    print("\n" + "=" * 50)
    print("🏁 Test completed!")


if __name__ == "__main__":
    main() 