#!/usr/bin/env python3

import sys
import os

print("🔍 Debugging Circular Import Issue")
print("==================================")

os.environ['THE_NEWS_API_API_KEY'] = 'DUMMY'
os.environ['ALPHA_VANTAGE_API_KEY'] = 'DUMMY'
os.environ['OPENAI_API_KEY'] = 'DUMMY'
os.environ['RAPIDAPI_KEY'] = 'DUMMY'
os.environ['BIZTOC_API_KEY'] = 'DUMMY'
os.environ['FINNHUB_API_KEY'] = 'DUMMY'
os.environ['FMP_API_KEY'] = 'DUMMY'
os.environ['NEWSDATA_IO_API_KEY'] = 'DUMMY'
os.environ['LOG_LEVEL'] = 'INFO'

sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

try:
    print("Attempting to import NewsCollector...")
    from data_collection.news_collector import NewsCollector
    print('✅ SUCCESS: NewsCollector imported')
    
    nc = NewsCollector()
    print('✅ SUCCESS: NewsCollector instantiated')
    
    methods = [m for m in dir(nc) if 'comprehensive' in m]
    print(f'✅ SUCCESS: Found methods: {methods}')
    
    if hasattr(nc, 'get_comprehensive_company_news'):
        print('✅ SUCCESS: get_comprehensive_company_news method exists')
        try:
            result = nc.get_comprehensive_company_news('AAPL')
            print(f'✅ SUCCESS: Method call returned {type(result)}')
        except Exception as e:
            print(f'⚠️  Method call error: {e}')
    else:
        print('❌ ERROR: get_comprehensive_company_news method missing')
        
except Exception as e:
    print(f'❌ ERROR: {e}')
    import traceback
    traceback.print_exc()
