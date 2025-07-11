import pytest

# NASDAQ-100 and S&P 500 symbols (truncated for brevity; use full lists in production)
NASDAQ_100 = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "PEP", "COST", "ADBE", "CSCO", "CMCSA", "AMD", "TXN", "AMGN", "INTC", "QCOM", "HON", "SBUX", "AMAT", "INTU", "ISRG", "BKNG", "VRTX", "REGN", "MDLZ", "GILD", "LRCX", "ADI", "MAR", "MU", "KDP", "ATVI", "ADP", "CTAS", "CSX", "PDD", "MELI", "KLAC", "CDNS", "AEP", "IDXX", "EXC", "ORLY", "MNST", "ROST", "PAYX", "XEL", "PCAR", "WBD", "TEAM", "DDOG", "ZS", "FTNT", "CRWD", "PANW", "SNPS", "MRVL", "DLTR", "ODFL", "CHTR", "SGEN", "BIDU", "LCID", "SIRI", "DOCU", "BIIB", "ILMN", "WDAY", "OKTA", "VRSK", "FANG", "FAST", "ANSS", "CTSH", "SWKS", "VRSN", "TTD", "BKR", "CEG", "CPRT", "GFS", "SPLK", "DDOG", "ZS", "FTNT", "CRWD", "PANW", "SNPS", "MRVL", "DLTR", "ODFL", "CHTR", "SGEN", "BIDU", "LCID", "SIRI", "DOCU", "BIIB", "ILMN", "WDAY", "OKTA", "VRSK", "FANG", "FAST", "ANSS", "CTSH", "SWKS", "VRSN", "TTD", "BKR", "CEG", "CPRT", "GFS", "SPLK"
]

SP500 = [
    "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "BRK.B", "UNH", "XOM", "JPM", "JNJ", "V", "LLY", "PG", "MA", "HD", "CVX", "ABBV", "MRK", "PEP", "AVGO", "COST", "ADBE", "KO", "MCD", "TMO", "CSCO", "WMT", "BAC", "ABT", "ACN", "DHR", "WFC", "LIN", "DIS", "VZ", "TXN", "UNP", "NEE", "PM", "ORCL", "BMY", "IBM", "AMGN", "LOW", "QCOM", "MDT", "RTX", "AMT", "INTC", "HON", "MMM", "GE", "UPS", "SBUX", "CVS", "CAT", "BLK", "GS", "AXP", "SPGI", "ISRG", "PLD", "DE", "TGT", "ADP", "SYK", "NOW", "MS", "BDX", "SCHW", "CI", "CB", "ZTS", "MO", "DUK", "SO", "PNC", "MMC", "C", "BKNG", "USB", "TFC", "GM", "HUM", "GILD", "AON", "FDX", "ITW", "CME", "NSC", "SHW", "ICE", "APD", "ADSK", "CL", "ETN", "EMR", "PSA", "EOG", "MCO", "PSX", "COF", "AEP", "D", "FISV", "FIS", "AIG", "TRV", "ALL", "MCK", "DOW", "ROP", "SRE", "HCA", "MPC", "AFL", "KMB", "VLO", "MAR", "OXY", "CNC", "KR", "TEL", "WELL", "ORLY", "HLT", "AWK", "STZ", "MTD", "PEG", "DLR", "SBAC", "CTSH", "VRSK", "CDNS", "PAYX", "WMB", "CTAS", "EXC", "XEL", "ODFL", "PCAR", "WBD", "TEAM", "DDOG", "ZS", "FTNT", "CRWD", "PANW", "SNPS", "MRVL", "DLTR", "ODFL", "CHTR", "SGEN", "BIDU", "LCID", "SIRI", "DOCU", "BIIB", "ILMN", "WDAY", "OKTA", "VRSK", "FANG", "FAST", "ANSS", "CTSH", "SWKS", "VRSN", "TTD", "BKR", "CEG", "CPRT", "GFS", "SPLK"
]

@pytest.fixture(scope="session")
def symbols():
    # Combine and deduplicate NASDAQ-100 and S&P 500 symbols
    return sorted(set(NASDAQ_100 + SP500))

@pytest.fixture(scope="session")
def market_data(symbols):
    # Provide dummy market data for each symbol
    return {symbol: {"price": 100.0, "volume": 1_000_000} for symbol in symbols}
