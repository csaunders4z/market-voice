from dotenv import load_dotenv
load_dotenv()
from src.config.settings import get_settings
s = get_settings()
print(f'NewsData key: {s.newsdata_io_api_key[:10]}...' if s.newsdata_io_api_key else 'NewsData key: None')