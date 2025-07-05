from dotenv import load_dotenv
# Load environment variables from .env file if it exists (for local development)
# In production/cloud environments, environment variables should be set directly
try:
    load_dotenv()
except FileNotFoundError:
    # No .env file found - this is expected in production/cloud environments
    pass
from src.config.settings import get_settings
s = get_settings()
print(f'NewsData key: {s.newsdata_api_key[:10]}...' if s.newsdata_api_key else 'NewsData key: None')
print(f'The News API key: {s.the_news_api_key[:10]}...' if s.the_news_api_key else 'The News API key: None') 