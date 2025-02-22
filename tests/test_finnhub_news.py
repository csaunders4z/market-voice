"""
News and error handling tests for Finnhub data source
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from src.data_sources.finnhub import FinnhubDataSource

MOCK_NEWS_RESPONSE = [
    {
        'headline': 'Test News 1',
        'source': 'Test Source 1'
    },
    {
        'headline': 'Test News 2',
        'source': 'Test Source 2'
    }
]

@pytest.fixture
def finnhub_source():
    """Create Finnhub source with mock API key"""
    with patch.dict(os.environ, {'FINNHUB_API_KEY': 'test_key'}):
        return FinnhubDataSource()

def test_get_news_success(finnhub_source):
    """Test successful news retrieval"""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_NEWS_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        
        result = finnhub_source.get_news('AAPL')
        
        assert result is not None
        assert 'Test News 1 (Test Source 1)' in result
        assert 'Test News 2 (Test Source 2)' in result

def test_get_news_empty_response(finnhub_source):
    """Test news retrieval with empty response"""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = []
        mock_get.return_value.raise_for_status = MagicMock()
        
        result = finnhub_source.get_news('AAPL')
        assert result is None

def test_api_error_handling(finnhub_source):
    """Test error handling for API requests"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception('API Error')
        
        result = finnhub_source.get_quote('AAPL')
        assert result is None  # Should handle error gracefully

def test_request_retry(finnhub_source):
    """Test that requests are retried on failure"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = [
            Exception('First failure'),
            Exception('Second failure'),
            MagicMock(
                json=lambda: {'c': 100, 'd': 1, 'dp': 1, 'v': 1000},
                raise_for_status=MagicMock()
            )
        ]
        
        result = finnhub_source.get_quote('AAPL')
        assert result is not None
        assert mock_get.call_count > 1  # Should have retried