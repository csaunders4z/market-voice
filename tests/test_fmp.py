"""
Tests for FMP data source implementation
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from src.data_sources.fmp import FMPDataSource

# Sample API responses
MOCK_QUOTE_RESPONSE = [{
    'price': 150.25,
    'change': 2.5,
    'changesPercentage': 1.67,
    'volume': 1000000,
    'avgVolume': 900000
}]

MOCK_PROFILE_RESPONSE = [{
    'companyName': 'Test Company',
    'sector': 'Technology',
    'industry': 'Software',
    'mktCap': 1000000000
}]

MOCK_NEWS_RESPONSE = [
    {
        'title': 'Test News 1',
        'site': 'Test Source 1'
    },
    {
        'title': 'Test News 2',
        'site': 'Test Source 2'
    }
]

@pytest.fixture
def fmp_source():
    """Create FMP source with mock API key"""
    with patch.dict(os.environ, {'FMP_API_KEY': 'test_key'}):
        return FMPDataSource()

def test_init_missing_api_key():
    """Test initialization fails without API key"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError):
            FMPDataSource()

def test_get_quote_success(fmp_source):
    """Test successful quote retrieval"""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_QUOTE_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        
        result = fmp_source.get_quote('AAPL')
        
        assert result is not None
        assert result['price'] == 150.25
        assert result['change'] == 2.5
        assert result['change_percent'] == 1.67
        assert result['volume'] == 1000000
        assert result['avg_volume'] == 900000

def test_get_quote_empty_response(fmp_source):
    """Test quote retrieval with empty response"""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = []
        mock_get.return_value.raise_for_status = MagicMock()
        
        result = fmp_source.get_quote('AAPL')
        assert result is None

def test_get_profile_success(fmp_source):
    """Test successful profile retrieval"""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_PROFILE_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        
        result = fmp_source.get_profile('AAPL')
        
        assert result is not None
        assert result['name'] == 'Test Company'
        assert result['sector'] == 'Technology'
        assert result['industry'] == 'Software'
        assert result['market_cap'] == 1000000000

def test_get_news_success(fmp_source):
    """Test successful news retrieval"""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_NEWS_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        
        result = fmp_source.get_news('AAPL')
        
        assert result is not None
        assert 'Test News 1 (Test Source 1)' in result
        assert 'Test News 2 (Test Source 2)' in result

def test_get_stock_data_full_success(fmp_source):
    """Test successful retrieval of all stock data"""
    with patch.object(fmp_source, 'get_quote') as mock_quote, \
         patch.object(fmp_source, 'get_profile') as mock_profile, \
         patch.object(fmp_source, 'get_news') as mock_news:
        
        mock_quote.return_value = {
            'price': 150.25,
            'change': 2.5,
            'change_percent': 3.0,  # >2% to trigger news fetch
            'volume': 1000000,
            'avg_volume': 900000
        }
        mock_profile.return_value = {
            'name': 'Test Company',
            'sector': 'Technology',
            'industry': 'Software',
            'market_cap': 1000000000
        }
        mock_news.return_value = 'Test News 1 (Test Source 1); Test News 2 (Test Source 2)'
        
        result = fmp_source.get_stock_data('AAPL')
        
        assert result is not None
        assert result['price'] == 150.25
        assert result['name'] == 'Test Company'
        assert 'Test News 1' in result['news']

def test_api_error_handling(fmp_source):
    """Test error handling for API requests"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception('API Error')
        
        result = fmp_source.get_quote('AAPL')
        assert result is None  # Should handle error gracefully

def test_request_retry(fmp_source):
    """Test that requests are retried on failure"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = [
            Exception('First failure'),
            Exception('Second failure'),
            MagicMock(
                json=lambda: MOCK_QUOTE_RESPONSE,
                raise_for_status=MagicMock()
            )
        ]
        
        result = fmp_source.get_quote('AAPL')
        assert result is not None
        assert mock_get.call_count > 1  # Should have retried