"""
Integration tests for Finnhub data source
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from src.data_sources.finnhub import FinnhubDataSource

@pytest.fixture
def finnhub_source():
    """Create Finnhub source with mock API key"""
    with patch.dict(os.environ, {'FINNHUB_API_KEY': 'test_key'}):
        return FinnhubDataSource()

def test_get_stock_data_full_success(finnhub_source):
    """Test successful retrieval of all stock data"""
    with patch.object(finnhub_source, 'get_quote') as mock_quote, \
         patch.object(finnhub_source, 'get_profile') as mock_profile, \
         patch.object(finnhub_source, 'get_news') as mock_news:
        
        mock_quote.return_value = {
            'price': 150.25,
            'change': 2.5,
            'change_percent': 3.0,  # >2% to trigger news fetch
            'volume': 1000000,
            'avg_volume': 0
        }
        mock_profile.return_value = {
            'name': 'Test Company',
            'sector': 'Technology',
            'industry': 'Technology',
            'market_cap': 1000000000
        }
        mock_news.return_value = 'Test News 1 (Test Source 1); Test News 2 (Test Source 2)'
        
        result = finnhub_source.get_stock_data('AAPL')
        
        assert result is not None
        assert result['price'] == 150.25
        assert result['name'] == 'Test Company'
        assert 'Test News 1' in result['news']

def test_get_stock_data_partial_success(finnhub_source):
    """Test stock data retrieval with some failing components"""
    with patch.object(finnhub_source, 'get_quote') as mock_quote, \
         patch.object(finnhub_source, 'get_profile') as mock_profile, \
         patch.object(finnhub_source, 'get_news') as mock_news:
        
        # Quote succeeds but others fail
        mock_quote.return_value = {
            'price': 150.25,
            'change': 2.5,
            'change_percent': 3.0,
            'volume': 1000000,
            'avg_volume': 0
        }
        mock_profile.return_value = None
        mock_news.return_value = None
        
        result = finnhub_source.get_stock_data('AAPL')
        
        assert result is not None
        assert result['price'] == 150.25
        assert 'name' not in result
        assert 'news' not in result