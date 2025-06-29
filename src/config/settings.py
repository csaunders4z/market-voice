"""
Configuration settings for Market Voices
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from datetime import time
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Keys
    alpha_vantage_api_key: str = Field(default_factory=lambda: "DUMMY" if os.getenv("TEST_MODE") == "1" else ..., env="ALPHA_VANTAGE_API_KEY")
    news_api_key: str = Field(default="", env="NEWS_API_KEY")  # Optional - can use other news sources
    openai_api_key: str = Field(default_factory=lambda: "DUMMY" if os.getenv("TEST_MODE") == "1" else ..., env="OPENAI_API_KEY")
    rapidapi_key: str = Field(default="", env="RAPIDAPI_KEY")  # Optional for Biztoc news
    biztoc_api_key: str = Field(default="", env="BIZTOC_API_KEY")
    finnhub_api_key: str = Field(default="", env="FINNHUB_API_KEY")
    fmp_api_key: str = Field(default="", env="FMP_API_KEY")
    
    # Data Collection Settings
    nasdaq_100_symbols: List[str] = Field(
        default=[
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "NFLX", 
            "ADBE", "CRM", "PYPL", "INTC", "AMD", "QCOM", "AVGO", "TXN", 
            "ORCL", "CSCO", "INTU", "IBM", "ADP", "VRTX", "REGN", "GILD",
            "ABNB", "UBER", "DASH", "ZM", "PTON", "ROKU", "SNAP", "TWTR",
            "PINS", "SQ", "SHOP", "ZM", "DOCU", "CRWD", "OKTA", "ZS",
            "PLTR", "SNOW", "DDOG", "NET", "MDB", "ESTC", "TEAM", "WDAY",
            "VEEV", "HUBS", "TWLO", "RNG", "ZM", "PTON", "ROKU", "SNAP",
            "PINS", "SQ", "SHOP", "ZM", "DOCU", "CRWD", "OKTA", "ZS",
            "PLTR", "SNOW", "DDOG", "NET", "MDB", "ESTC", "TEAM", "WDAY",
            "VEEV", "HUBS", "TWLO", "RNG", "ZM", "PTON", "ROKU", "SNAP",
            "PINS", "SQ", "SHOP", "ZM", "DOCU", "CRWD", "OKTA", "ZS",
            "PLTR", "SNOW", "DDOG", "NET", "MDB", "ESTC", "TEAM", "WDAY"
        ],
        env="NASDAQ_100_SYMBOLS"
    )
    
    @field_validator('nasdaq_100_symbols', mode='before')
    @classmethod
    def parse_nasdaq_symbols(cls, v):
        """Parse NASDAQ symbols from comma-separated string or list"""
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [symbol.strip() for symbol in v.split(',') if symbol.strip()]
        return v
    
    # Market Hours (EST)
    market_open_time: time = Field(default=time(9, 30), env="MARKET_OPEN_TIME")
    market_close_time: time = Field(default=time(16, 0), env="MARKET_CLOSE_TIME")
    
    # Content Settings
    target_runtime_minutes: int = Field(default=12, env="TARGET_RUNTIME_MINUTES")
    min_runtime_minutes: int = Field(default=10, env="MIN_RUNTIME_MINUTES")
    max_runtime_minutes: int = Field(default=15, env="MAX_RUNTIME_MINUTES")
    
    # Host Personalities
    marcus_personality: str = Field(
        default="25-year-old energetic analyst with a fresh perspective on markets",
        env="MARCUS_PERSONALITY"
    )
    suzanne_personality: str = Field(
        default="31-year-old former Wall Street trader with deep market knowledge",
        env="SUZANNE_PERSONALITY"
    )
    
    # Script Generation
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    max_tokens: int = Field(default=4000, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    
    # Data Collection Thresholds
    significant_move_threshold: float = Field(default=2.0, env="SIGNIFICANT_MOVE_THRESHOLD")
    volume_threshold_multiplier: float = Field(default=2.0, env="VOLUME_THRESHOLD_MULTIPLIER")
    news_recency_hours: int = Field(default=24, env="NEWS_RECENCY_HOURS")
    
    # Quality Controls
    max_phrase_repetitions: int = Field(default=2, env="MAX_PHRASE_REPETITIONS")
    max_terminology_usage: int = Field(default=3, env="MAX_TERMINOLOGY_USAGE")
    speaking_time_tolerance: float = Field(default=0.05, env="SPEAKING_TIME_TOLERANCE")
    
    # Rate Limiting Settings
    fmp_rate_limit_delay: float = Field(default=0.5, env="FMP_RATE_LIMIT_DELAY")  # Seconds between FMP calls
    fmp_batch_size: int = Field(default=10, env="FMP_BATCH_SIZE")  # Symbols per batch
    fmp_batch_delay: float = Field(default=2.0, env="FMP_BATCH_DELAY")  # Delay between batches
    fmp_max_retries: int = Field(default=3, env="FMP_MAX_RETRIES")  # Max retries per symbol
    
    yahoo_rate_limit_delay: float = Field(default=0.2, env="YAHOO_RATE_LIMIT_DELAY")  # Seconds between Yahoo calls
    yahoo_batch_size: int = Field(default=20, env="YAHOO_BATCH_SIZE")  # Symbols per batch
    yahoo_batch_delay: float = Field(default=1.0, env="YAHOO_BATCH_DELAY")  # Delay between batches
    
    alpha_vantage_rate_limit_delay: float = Field(default=12.0, env="AV_RATE_LIMIT_DELAY")  # Seconds between AV calls
    alpha_vantage_batch_size: int = Field(default=5, env="AV_BATCH_SIZE")  # Symbols per batch (5 calls/minute limit)
    alpha_vantage_batch_delay: float = Field(default=60.0, env="AV_BATCH_DELAY")  # 1 minute between batches
    
    # Adaptive Rate Limiting
    enable_adaptive_rate_limiting: bool = Field(default=True, env="ENABLE_ADAPTIVE_RATE_LIMITING")
    rate_limit_backoff_multiplier: float = Field(default=2.0, env="RATE_LIMIT_BACKOFF_MULTIPLIER")
    max_rate_limit_delay: float = Field(default=30.0, env="MAX_RATE_LIMIT_DELAY")  # Max delay in seconds
    
    # Collection Limits
    max_symbols_per_collection: int = Field(default=50, env="MAX_SYMBOLS_PER_COLLECTION")  # Max symbols to collect
    collection_timeout_minutes: int = Field(default=10, env="COLLECTION_TIMEOUT_MINUTES")  # Max collection time
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/market_voices.log", env="LOG_FILE")
    
    # Database
    database_url: str = Field(default="sqlite:///market_voices.db", env="DATABASE_URL")
    
    # Output
    output_directory: str = Field(default="output", env="OUTPUT_DIRECTORY")
    script_output_file: str = Field(default="daily_script.txt", env="SCRIPT_OUTPUT_FILE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Remove global settings instance
# settings = Settings()

_settings_instance = None

def get_settings():
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance 