# Market Voices - Setup Guide

This guide will help you set up and run the Market Voices automated stock market video generation system.

## Prerequisites

### 1. Python Installation
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
  - During installation, **check "Add Python to PATH"**
  - Restart your terminal after installation
- **macOS**: Use Homebrew: `brew install python`
- **Linux**: Usually pre-installed, or use package manager

### 2. API Keys Required
You'll need API keys for the following services:

#### Alpha Vantage (Stock Data)
- **Cost**: Free tier available (500 requests/day)
- **Sign up**: [alphavantage.co](https://www.alphavantage.co/support/#api-key)
- **Purpose**: Real-time stock market data

#### News API (News Integration)
- **Cost**: Free tier available (1,000 requests/day)
- **Sign up**: [newsapi.org](https://newsapi.org/register)
- **Purpose**: Financial news for context

#### OpenAI (Script Generation)
- **Cost**: Pay-per-use (typically $0.01-0.10 per script)
- **Sign up**: [platform.openai.com](https://platform.openai.com/api-keys)
- **Purpose**: AI-powered script generation

## Installation Steps

### Step 1: Clone/Download the Project
```bash
# If using git
git clone <repository-url>
cd market-voices

# Or download and extract the ZIP file
```

### Step 2: Install Dependencies

#### Windows (PowerShell)
```powershell
# Run the setup script
.\setup.ps1

# Or manually:
python -m pip install -r requirements.txt
```

#### Windows (Command Prompt)
```cmd
# Run the setup script
setup.bat

# Or manually:
pip install -r requirements.txt
```

#### macOS/Linux
```bash
# Install dependencies
pip3 install -r requirements.txt

# Or if you prefer virtual environment:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

1. **Copy the example configuration:**
   ```bash
   cp config.env.example .env
   ```

2. **Edit the .env file** with your API keys:
   ```bash
   # Windows
   notepad .env

   # macOS/Linux
   nano .env
   ```

3. **Add your API keys:**
   ```bash
   ALPHA_VANTAGE_API_KEY=your_actual_key_here
   NEWS_API_KEY=your_actual_key_here
   OPENAI_API_KEY=your_actual_key_here
   ```

### Step 4: Test the System

```bash
# Test without API keys (uses sample data)
python test_system.py

# Test with API keys
python main.py --test
```

## Usage

### Production Mode
```bash
# Run the complete daily workflow
python main.py
```

### Test Mode
```bash
# Run with sample data (no API calls)
python main.py --test
```

## Output Files

After running the system, check the `output/` directory for:

- **`market_data_YYYYMMDD_HHMMSS.json`** - Raw market data
- **`script_YYYYMMDD_HHMMSS.json`** - Generated script (JSON)
- **`script_formatted_YYYYMMDD_HHMMSS.txt`** - Human-readable script
- **`quality_report_YYYYMMDD_HHMMSS.json`** - Quality validation
- **`daily_summary_YYYYMMDD_HHMMSS.txt`** - Summary report

## Troubleshooting

### Common Issues

#### 1. "Python was not found"
**Solution**: Install Python and add to PATH
- Download from [python.org](https://www.python.org/downloads/)
- Check "Add Python to PATH" during installation
- Restart your terminal

#### 2. Import Errors
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

#### 3. API Key Errors
**Solution**: Verify your .env file
```bash
# Check if .env exists
ls .env

# Verify API keys are set
cat .env
```

#### 4. Network/API Errors
**Solutions**:
- Check internet connection
- Verify API keys are correct
- Check API rate limits
- Try test mode first: `python main.py --test`

### Logs
Check detailed logs in `logs/market_voices.log`:
```bash
# View recent logs
tail -f logs/market_voices.log

# Windows
type logs\market_voices.log
```

## Configuration Options

### Host Schedule
- **Monday**: Suzanne leads (15 min)
- **Tuesday**: Suzanne leads (15 min)
- **Wednesday**: Marcus leads (15 min)
- **Thursday**: Suzanne leads (10 min)
- **Friday**: Marcus leads (10 min)

### Quality Settings
- **Phrase repetition limit**: 2 times
- **Terminology usage limit**: 3 times per episode
- **Speaking time balance**: 45-55% per host
- **Content freshness**: <24 hours

## Next Steps

### Phase 1 (Current)
- ✅ Data collection
- ✅ Script generation
- ✅ Quality validation
- ✅ Basic output

### Phase 2 (Future)
- 📊 News integration
- 📈 Technical indicators
- 🎯 Enhanced quality controls

### Phase 3 (Future)
- 🎥 Video generation
- 📊 Visual charts
- 🎵 Audio production

## Support

If you encounter issues:

1. **Check the logs**: `logs/market_voices.log`
2. **Run tests**: `python test_system.py`
3. **Verify setup**: Follow this guide step-by-step
4. **Check API keys**: Ensure all keys are valid and have credits
5. **Try test mode**: `python main.py --test`

## Cost Estimation

### Monthly Costs (Estimated)
- **Alpha Vantage**: $0 (free tier)
- **News API**: $0 (free tier)
- **OpenAI**: $5-20 (depending on usage)
- **Total**: $5-20/month

### Scaling Costs
- **100 scripts/month**: ~$10-15
- **500 scripts/month**: ~$25-50
- **1000 scripts/month**: ~$50-100

## Success Metrics

### Technical KPIs
- Data collection success rate: >95%
- Script generation time: <5 minutes
- System uptime: >99% during trading days

### Quality KPIs
- Factual accuracy: Zero errors
- Speaking time balance: 45-55%
- Content freshness: <24 hours

### Business KPIs
- Daily uploads: 5/week
- Manual intervention: <10 minutes
- Revenue potential: $500-5000/month

---

**Ready to start?** Run `python test_system.py` to verify your setup! 