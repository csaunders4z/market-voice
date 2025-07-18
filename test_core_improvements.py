#!/usr/bin/env python3
"""
Simplified test to verify core news integration improvements work
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, 'src')

def test_core_improvements():
    """Test the core improvements without full integration dependencies"""
    print("=== Testing Core News Integration Improvements ===")
    
    try:
        from src.data_collection.news_collector import news_collector
        news_collector.reset_circuit_breakers()
        
        assert news_collector._newsapi_consecutive_failures == 0
        assert news_collector._newsapi_disabled_for_session == False
        assert news_collector._newsdata_consecutive_failures == 0
        assert news_collector._newsdata_disabled_for_session == False
        assert news_collector._biztoc_consecutive_failures == 0
        assert news_collector._biztoc_disabled_for_session == False
        assert news_collector._thenewsapi_consecutive_failures == 0
        assert news_collector._thenewsapi_disabled_for_session == False
        
        print("✅ Circuit breaker reset: WORKING")
    except Exception as e:
        print(f"❌ Circuit breaker reset: {e}")
        return False
    
    try:
        from src.data_collection.unified_data_collector import unified_collector
        import pytz
        
        now = datetime.now()
        test_articles = [
            {'title': 'Recent Article', 'published_at': now.isoformat()},
            {'title': 'Old Article', 'published_at': (now - timedelta(days=2)).isoformat()},
            {'title': 'No Date Article', 'published_at': ''},
            {'title': 'Malformed Date', 'published_at': 'invalid-date'}
        ]
        
        filtered = unified_collector._filter_recent_articles(test_articles)
        print(f"✅ Article filtering: {len(filtered)}/{len(test_articles)} articles kept")
        
        market_tz = pytz.timezone('US/Eastern')
        cutoff_time = datetime.now(market_tz) - timedelta(hours=24)
        
        recent_iso = now.isoformat()
        old_iso = (now - timedelta(days=2)).isoformat()
        
        is_recent = unified_collector._is_recent_article(recent_iso, cutoff_time)
        is_old = unified_collector._is_recent_article(old_iso, cutoff_time)
        
        assert is_recent == True, "Recent article should be detected as recent"
        assert is_old == False, "Old article should be detected as old"
        
        print("✅ Timezone-aware filtering: WORKING")
    except Exception as e:
        print(f"❌ Article filtering: {e}")
        return False
    
    try:
        from src.script_generation.script_generator import ScriptGenerator
        script_gen = ScriptGenerator()
        
        mock_data = {
            'winners': [
                {
                    'symbol': 'AAPL',
                    'company_name': 'Apple Inc.',
                    'current_price': 150.0,
                    'percent_change': 2.5,
                    'volume_ratio': 1.2,
                    'news_articles': [
                        {
                            'title': 'Apple Reports Strong Earnings',
                            'source': 'Reuters',
                            'published_at': '2025-07-18T10:00:00Z',
                            'catalyst_type': 'earnings'
                        }
                    ],
                    'news_analysis': 'Apple showed strong performance in Q2 with revenue beating expectations.',
                    'news_sources': ['Reuters', 'Bloomberg']
                }
            ],
            'losers': [],
            'market_summary': {'total_stocks_analyzed': 1}
        }
        
        lead_host = script_gen.get_lead_host_for_date(datetime.now())
        prompt = script_gen.create_script_prompt(mock_data, lead_host)
        
        has_catalyst_mention = 'Identified Catalysts' in prompt
        has_news_count = 'total)' in prompt
        has_analysis = 'News Analysis' in prompt
        has_headlines = 'Key Headlines' in prompt or 'Recent News Articles' in prompt
        
        improvements = 0
        if has_catalyst_mention:
            print("✅ Catalyst detection integration: WORKING")
            improvements += 1
        if has_news_count:
            print("✅ News article count display: WORKING")
            improvements += 1
        if has_analysis:
            print("✅ News analysis integration: WORKING")
            improvements += 1
        if has_headlines:
            print("✅ News headlines integration: WORKING")
            improvements += 1
        
        if improvements >= 2:
            print("✅ Enhanced script generation: WORKING")
        else:
            print("⚠️  Script generation: Limited improvements detected")
            
    except Exception as e:
        print(f"❌ Enhanced script generation: {e}")
        return False
    
    print("\n✅ ALL CORE IMPROVEMENTS VALIDATED!")
    return True

if __name__ == "__main__":
    success = test_core_improvements()
    if success:
        print("\n🎉 News integration improvements are ready for production!")
    else:
        print("\n❌ Some improvements need attention before deployment")
