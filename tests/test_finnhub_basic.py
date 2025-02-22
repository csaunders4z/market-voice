"""
Basic tests for Finnhub data source implementation
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from src.data_sources.finnhub import FinnhubDataSource

# Sample API responses
MOCK_QUOTE_RESPONSE = {
    'c': 150.25,  # Current price
    'd': 2.5,    # Change
    'dp': 1.67,  # Percent change
    'v': 1000000 # Volume
}

MOCK_PROFILE_RESPONSE = {
    'name': 'Test Company',
    'finnhubIndustry': 'Technology',
    'marketCapitalization': 1000  # Will be multiplied by 1M
}

@pytest.fixture
def finnhub_source():
    """Create Finnhub source with mock API key"""
    with patch.dict(os.environ, {'FINNHUB_API_KEY': 'test_key'}):
        return FinnhubDataSource()

def test_init_missing_api_key():
    """Test initialization fails without API key"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError):
            FinnhubDataSource()

def test_get_quote_success(finnhub_source):
    """Test successful quote retrieval"""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_QUOTE_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        
        result = finnhub_source.get_quote('AAPL')
        
        assert result is not None
        assert result['price'] == 150.25
        assert result['change'] == 2.5
        assert result['change_percent'] == 1.67
        assert result['volume'] == 1000000
        assert result['avg_volume'] == 0  # Not provided by Finnhub

def test_get_profile_success(finnhub_source):
    """Test successful profile retrieval"""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_PROFILE_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        
        result = finnhub_source.get_profile('AAPL')
        
        assert result is not None
        assert result['name'] == 'Test Company'
        assert result['sector'] == 'Technology'
        assert result['industry'] == 'Technology'
        assert result['market_cap'] == 1000000000  # 1000 * 1M