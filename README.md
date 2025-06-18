# Market Voices

An automated stock market video generation system that creates daily financial news content covering NASDAQ-100 performance with two AI hosts.

## ⚠️ CRITICAL: API Key Safety

**IMPORTANT**: This project contains sensitive API keys. Follow these safety protocols:

### 🔐 API Key Protection
- **NEVER commit `.env` files to version control**
- **ALWAYS backup before making changes**: `.\backup_env.ps1`
- **Use the safe setup script**: `.\setup_env.ps1`
- **Keep API keys secure and private**

### 🛡️ Safety Scripts
```powershell
# Create backup before changes
.\backup_env.ps1

# Safe environment setup
.\setup_env.ps1

# Check what's being tracked by git
git status
```

### 📁 Protected Files
The following files are automatically ignored by git:
- `.env` (contains your API keys)
- `output/` (generated content)
- `logs/` (system logs)
- `backups/` (environment backups)

## Project Overview

Market Voices generates professional financial news videos with:
- **Marcus**: 25-year-old energetic analyst (leads Wed/Fri)
- **Suzanne**: 31-year-old former Wall Street trader (leads Mon/Tue/Thu)
- **Content**: Daily NASDAQ-100 analysis, top 5 winners/losers, market insights
- **Runtime**: 10-15 minutes per episode
- **Schedule**: Weekdays after market close

## Features

### Phase 1 (MVP) - MUST HAVE
- ✅ Automated NASDAQ-100 data collection
- ✅ Top 5 winners/bottom 5 losers identification
- ✅ Two-host script generation with personality consistency
- ✅ Professional financial news tone
- ✅ Error handling and logging
- ✅ Factual accuracy validation

### Phase 2 - SHOULD HAVE
- 📊 News integration for significant movers
- 📈 Technical indicators (RSI, MACD, volume analysis)
- 🎯 Content quality controls (repetition detection, speaking time balance)
- 🔄 Multi-source data validation

### Phase 3 - COULD HAVE
- 🎥 Automated video generation with ElevenLabs
- 📊 Chart and visual content creation
- 🎵 Professional intro/outro music
- 📱 Auto-captions and thumbnail generation

## Quick Start

### 1. Prerequisites
- Python 3.8 or higher
- API keys for:
  - [Alpha Vantage](https://www.alphavantage.co/support/#api-key) (stock data)
  - [News API](https://newsapi.org/register) (news integration)
  - [OpenAI](https://platform.openai.com/api-keys) (script generation)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd market-voices

# Install dependencies
pip install -r requirements.txt

# Test the system
python test_system.py
```

### 3. Configuration

```bash
# Copy the example configuration
cp config.env.example .env

# Edit .env with your API keys
nano .env
```

Required environment variables:
```bash
ALPHA_VANTAGE_API_KEY=your_key_here
NEWS_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### 4. Run the System

```bash
# Test mode (uses sample data, no API calls)
python main.py --test

# Production mode (requires API keys)
python main.py
```

## Project Structure

```
market_voices/
├── src/
│   ├── config/              # Configuration management
│   │   └── settings.py      # Application settings
│   ├── data_collection/     # Stock data fetching
│   │   └── stock_data.py    # NASDAQ-100 data collection
│   ├── script_generation/   # AI script creation
│   │   ├── host_manager.py  # Host personalities & rotation
│   │   └── script_generator.py # OpenAI script generation
│   ├── content_validation/  # Quality controls
│   │   └── quality_controls.py # Script validation
│   └── utils/              # Shared utilities
│       └── logger.py       # Logging configuration
├── config.env.example      # Environment template
├── requirements.txt        # Python dependencies
├── main.py                # Main application
├── test_system.py         # System test script
└── README.md              # This file
```

## Usage Examples

### Basic Usage
```bash
# Run the complete daily workflow
python main.py

# Run in test mode (no API keys required)
python main.py --test
```

### Output Files
The system generates several output files in the `output/` directory:
- `market_data_YYYYMMDD_HHMMSS.json` - Raw market data
- `script_YYYYMMDD_HHMMSS.json` - Generated script (JSON format)
- `script_formatted_YYYYMMDD_HHMMSS.txt` - Human-readable script
- `quality_report_YYYYMMDD_HHMMSS.json` - Quality validation results
- `daily_summary_YYYYMMDD_HHMMSS.txt` - Summary report

### Sample Output
```