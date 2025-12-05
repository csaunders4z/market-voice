# Quick Start - Ubuntu Agent

## 🚀 Essential Commands (Run in Order)

```bash
# 1. Verify location
pwd && ls -la

# 2. Install system packages
sudo apt update && sudo apt install python3 python3-pip python3-venv git -y

# 3. Setup Python environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Setup config
cp config.env.example .env
mkdir -p logs output

# 6. Configure API keys (CRITICAL)
nano .env
# Add your API keys here

# 7. Test system
python test_system.py
python test_enhanced_system.py
python main.py --test
```

## 🔑 Required API Keys (.env file)
```
ALPHA_VANTAGE_API_KEY=your_key
NEWS_API_KEY=your_key  
OPENAI_API_KEY=your_key
RAPIDAPI_KEY=your_key
```

## ✅ Success Indicators
- Virtual environment shows `(venv)` prefix
- All tests pass without errors
- Output files created in `output/` directory
- Logs written to `logs/` directory

## 🆘 If Something Fails
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version
python3 --version

# Verify .env file
cat .env
```

**Start with Step 1 and report back after each step!** 