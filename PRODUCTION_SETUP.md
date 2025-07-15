# Market Voices Production Setup Guide

## Required API Keys for Production

To run Market Voices in production mode, you need to configure the following API keys in your `.env` file:

### Essential APIs (Required)
1. **OpenAI API Key** - For script generation
   - Get from: https://platform.openai.com/api-keys
   - Environment variable: `OPENAI_API_KEY`

2. **Alpha Vantage API Key** - For stock data fallback
   - Get from: https://www.alphavantage.co/support/#api-key
   - Environment variable: `ALPHA_VANTAGE_API_KEY`

3. **Financial Modeling Prep (FMP) API Key** - Primary stock data source
   - Get from: https://financialmodelingprep.com/developer/docs
   - Environment variable: `FMP_API_KEY`

### News APIs (At least one required)
4. **The News API** - For financial news
   - Get from: https://www.thenewsapi.com/
   - Environment variable: `THE_NEWS_API_API_KEY`

5. **NewsAPI** - Alternative news source
   - Get from: https://newsapi.org/
   - Environment variable: `NEWS_API_KEY`

### Optional APIs (Enhance functionality)
6. **Finnhub API Key** - Additional market data
   - Environment variable: `FINNHUB_API_KEY`

7. **NewsData.io API Key** - Additional news source
   - Environment variable: `NEWSDATA_IO_API_KEY`

## Configuration Steps

1. Copy the template: `cp env.template .env`
2. Edit `.env` and replace placeholder values with your actual API keys
3. Install optional dependencies (if needed): `pip install -r requirements-optional.txt`
4. Never commit the `.env` file to version control
5. Test configuration: `python validate_production.py`
6. Run health check: `python main.py --health`

## Security Notes
- Keep API keys secure and never share them
- Use environment variables in production deployments
- Monitor API usage and costs regularly

## Production Deployment Process

### Using production_deploy.py Script
The repository includes a `production_deploy.py` script for production deployment:

```bash
# Run deployment (requires sudo for system-level configuration)
sudo python production_deploy.py
```

The deploy script will:
- Create system directories in `/etc/market-voices/`
- Copy configuration files
- Set up proper file permissions
- Configure systemd service
- Validate deployment

### Manual Production Setup
If you prefer manual setup:

1. **Create production directory structure:**
   ```bash
   sudo mkdir -p /etc/market-voices
   sudo mkdir -p /var/log/market-voices
   sudo mkdir -p /var/lib/market-voices/output
   ```

2. **Copy and configure environment:**
   ```bash
   sudo cp .env /etc/market-voices/.env
   sudo chmod 600 /etc/market-voices/.env
   sudo chown root:root /etc/market-voices/.env
   ```

3. **Set up logging:**
   ```bash
   sudo touch /var/log/market-voices/market_voice.log
   sudo chmod 644 /var/log/market-voices/market_voice.log
   ```

### Environment Variables for Production
When deploying to production systems, you can also use environment variables directly:

```bash
export OPENAI_API_KEY="your-actual-openai-key"
export ALPHA_VANTAGE_API_KEY="your-actual-alpha-vantage-key"
export THE_NEWS_API_API_KEY="your-actual-news-api-key"
export FMP_API_KEY="your-actual-fmp-key"
```

## Testing Production Configuration

### 1. Validate System Configuration
```bash
python validate_production.py
```

### 2. Run Health Check
```bash
python main.py --health
```

### 3. Test Production Mode (with real API keys)
```bash
python main.py
```

### 4. Test Mode (for development/testing)
```bash
python main.py --test
```

## Monitoring and Maintenance

### Cost Monitoring
The system includes built-in cost tracking for API usage. Monitor costs regularly through:
- Daily summary reports in output directory
- Log files for detailed API usage
- Built-in budget monitoring alerts

### Health Checks
Regular health checks should be performed:
- API connectivity tests
- System resource monitoring
- Output quality validation

### Log Management
Production logs are stored in:
- `/var/log/market-voices/` (production deployment)
- `logs/` directory (development)

Configure log rotation to prevent disk space issues:
```bash
sudo logrotate /etc/logrotate.d/market-voices
```

## Troubleshooting

### Common Issues
1. **API Key Errors**: Verify keys are correctly configured and have sufficient quotas
2. **Permission Errors**: Ensure proper file permissions for production directories
3. **Network Issues**: Check firewall settings for API access
4. **Memory Issues**: Monitor system resources during large data collection

### Support
- Check logs in `/var/log/market-voices/` for detailed error information
- Use `python main.py --health` for system diagnostics
- Review API provider documentation for service-specific issues
