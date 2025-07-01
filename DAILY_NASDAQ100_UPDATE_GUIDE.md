# Daily NASDAQ-100 Symbol Update System

## Overview

The Market Voices project now includes an automated daily update system for NASDAQ-100 symbols. This system ensures that your symbol lists are always current and up-to-date with the latest index constituents.

## Features

- ✅ **Automated daily updates** at 6:00 AM
- ✅ **Multiple reliable sources** with fallback options
- ✅ **Primary source**: StockAnalysis.com (your recommended backup)
- ✅ **Fallback sources**: Wikipedia, FMP API, hardcoded list
- ✅ **Smart caching** (only updates if >12 hours since last update)
- ✅ **Comprehensive validation** of fetched symbols
- ✅ **Detailed logging** with rotation and retention
- ✅ **Cron job automation** for hands-off operation

## Quick Setup

### 1. Run the Setup Script

```bash
./setup_daily_nasdaq100_cron.sh
```

This script will:
- Detect your Python installation
- Create a cron job that runs daily at 6:00 AM
- Set up proper logging
- Ask for confirmation before making changes

### 2. Manual Test

Test the update system manually:

```bash
python daily_nasdaq100_update.py
```

Expected output:
```
21:24:45 | INFO | Starting daily NASDAQ-100 symbol update...
21:24:45 | INFO | Successfully fetched 101 NASDAQ-100 symbols
21:24:45 | INFO | 🎉 Daily NASDAQ-100 update completed successfully!
```

## How It Works

### Data Sources (in order of preference)

1. **StockAnalysis.com** (Primary)
   - URL: https://stockanalysis.com/list/nasdaq-100-stocks/
   - Your recommended backup source
   - Provides 101 symbols with current price data

2. **Wikipedia** (Fallback)
   - URL: https://en.wikipedia.org/wiki/Nasdaq-100
   - Reliable public source
   - Updated by community

3. **FMP API** (Fallback)
   - Requires API key
   - Official financial data provider

4. **Hardcoded List** (Emergency Fallback)
   - Built-in list of current symbols
   - Ensures system never fails completely

### Update Logic

- **Frequency**: Daily at 6:00 AM
- **Smart Caching**: Only updates if >12 hours since last update
- **Validation**: Ensures at least 95 symbols are fetched
- **Critical Symbols Check**: Verifies major stocks (AAPL, MSFT, etc.) are present
- **Duplicate Detection**: Removes any duplicate symbols

### File Structure

```
src/data_collection/symbol_lists/
├── current_symbols.json          # Latest symbol data
├── comprehensive_symbols_YYYYMMDD_HHMMSS.json  # Timestamped backups
├── nasdaq100_symbols_YYYYMMDD_HHMMSS.txt       # NASDAQ-100 only
├── sp500_symbols_YYYYMMDD_HHMMSS.txt           # S&P 500 only
└── all_symbols_YYYYMMDD_HHMMSS.txt             # Combined list

logs/
├── daily_nasdaq100_update.log    # Manual run logs
└── cron_nasdaq100_update.log     # Automated run logs
```

## Monitoring and Maintenance

### View Current Status

```bash
# Check last update time
python -c "
import json
with open('src/data_collection/symbol_lists/current_symbols.json') as f:
    data = json.load(f)
    print(f'Last updated: {data["last_updated"]}')
    print(f'NASDAQ-100 symbols: {data["nasdaq100_count"]}')
    print(f'S&P 500 symbols: {data["sp500_count"]}')
    print(f'Total unique symbols: {data["total_symbols"]}')
"
```

### View Logs

```bash
# View recent manual update logs
tail -f logs/daily_nasdaq100_update.log

# View recent automated update logs
tail -f logs/cron_nasdaq100_update.log

# View all logs
ls -la logs/
```

### Cron Job Management

```bash
# View current cron jobs
crontab -l

# Edit cron jobs
crontab -e

# Remove all cron jobs
crontab -r
```

### Manual Update

```bash
# Force update (ignores cache)
python daily_nasdaq100_update.py

# Test symbol loader
python -c "
from src.data_collection.symbol_loader import SymbolLoader
loader = SymbolLoader()
loader.update_symbols()
print(f'NASDAQ-100: {len(loader.get_nasdaq_100_symbols())} symbols')
print(f'S&P 500: {len(loader.get_sp_500_symbols())} symbols')
print(f'Total: {len(loader.get_all_symbols())} symbols')
"
```

## Troubleshooting

### Common Issues

#### 1. "Failed to fetch NASDAQ-100 symbols from any source"

**Cause**: All data sources are unavailable
**Solution**: 
- Check internet connectivity
- Verify StockAnalysis.com is accessible
- Check if Wikipedia is blocked
- Review logs for specific error messages

#### 2. "NASDAQ-100 count too low"

**Cause**: Fetched fewer than 95 symbols
**Solution**:
- Check if StockAnalysis.com page structure changed
- Verify parsing logic in `_fetch_nasdaq100_from_stockanalysis()`
- Review logs for parsing errors

#### 3. "Missing critical symbols"

**Cause**: Major stocks like AAPL, MSFT missing
**Solution**:
- Check if symbols were renamed
- Verify data source is current
- Review symbol cleaning logic

#### 4. Cron job not running

**Cause**: Cron service issues or incorrect setup
**Solution**:
```bash
# Check cron service status
sudo systemctl status cron

# Restart cron service
sudo systemctl restart cron

# Check cron logs
sudo tail -f /var/log/cron
```

### Debug Mode

Enable detailed logging:

```bash
# Edit the script to add debug logging
sed -i 's/level="INFO"/level="DEBUG"/' daily_nasdaq100_update.py

# Run with debug output
python daily_nasdaq100_update.py
```

### Emergency Recovery

If all sources fail, the system will use the hardcoded fallback list:

```python
# The fallback list includes current major NASDAQ-100 stocks
fallback_symbols = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX",
    "ADBE", "CRM", "PYPL", "INTC", "AMD", "QCOM", "AVGO", "TXN",
    # ... and many more
]
```

## Integration with Market Voices

The updated symbols are automatically used by:

1. **Symbol Loader** (`src/data_collection/symbol_loader.py`)
   - Provides symbols to all data collectors
   - Caches results for performance

2. **FMP Stock Data Collector** (`src/data_collection/fmp_stock_data.py`)
   - Uses updated symbols for API calls
   - Falls back to current list if API fails

3. **Screening Module** (`src/data_collection/screening_module.py`)
   - Screens updated symbols for market movers

4. **Comprehensive Collector** (`src/data_collection/comprehensive_collector.py`)
   - Collects data for all updated symbols

## Performance Impact

- **Update Time**: ~30-60 seconds daily
- **Storage**: ~50KB per update (with 7-day retention)
- **CPU**: Minimal impact during update
- **Network**: ~1MB per update (HTTP requests)

## Security Considerations

- **No API keys required** for primary sources
- **Public data sources** only
- **Read-only operations** (no data modification)
- **Log rotation** prevents disk space issues
- **Error handling** prevents system crashes

## Future Enhancements

Potential improvements:

1. **Email notifications** for failed updates
2. **Webhook integration** for external monitoring
3. **Symbol change detection** (additions/removals)
4. **Market hours awareness** (avoid updates during trading)
5. **Multiple update times** (pre-market, post-market)
6. **Symbol validation** against real-time data

## Support

For issues or questions:

1. Check the logs first: `tail -f logs/daily_nasdaq100_update.log`
2. Review this documentation
3. Test manually: `python daily_nasdaq100_update.py`
4. Check system resources and connectivity

---

**Last Updated**: June 30, 2025  
**Version**: 1.0  
**Maintainer**: Market Voices Development Team 