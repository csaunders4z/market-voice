# Ubuntu Agent Instructions - Market Voices Setup

## Current Status
- ✅ Project repository cloned
- ✅ Project structure verified (all directories and files present)
- ✅ API keys need to be configured in .env file
- ⏳ Dependencies need to be installed
- ⏳ System needs to be tested

## Immediate Next Steps

### 1. Verify Current Directory and Project Structure
```bash
pwd
ls -la
```

**Expected**: Should show the Market Voices project files including `main.py`, `requirements.txt`, `src/` directory, etc.

### 2. Install System Dependencies
```bash
# Update package list
sudo apt update

# Install required system packages
sudo apt install python3 python3-pip python3-venv git curl wget nano -y
```

### 3. Create Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation (should show venv path)
which python
```

### 4. Install Python Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt
```

### 5. Set Up Environment Configuration
```bash
# Create .env file from template
cp config.env.example .env

# Create necessary directories
mkdir -p logs output
```

### 6. Configure API Keys
**CRITICAL**: The user mentioned they have entered their secrets. You need to:

1. **Check if .env file exists and has content:**
   ```bash
   ls -la .env
   cat .env
   ```

2. **If .env is empty or missing, create it with the required API keys:**
   ```bash
   nano .env
   ```

3. **Required API keys to add:**
   ```
   ALPHA_VANTAGE_API_KEY=your_actual_key_here
   NEWS_API_KEY=your_actual_key_here
   OPENAI_API_KEY=your_actual_key_here
   RAPIDAPI_KEY=your_actual_key_here
   ```

   **Note**: Ask the user for these keys if not already provided.

### 7. Test System Components
```bash
# Basic system test (tests imports and structure)
python test_system.py

# Enhanced test with mock data
python test_enhanced_system.py

# Test production workflow in test mode
python main.py --test
```

### 8. Verify All Tests Pass
**Expected Results:**
- All import tests should pass
- Directory structure should be valid
- Host manager should work
- Quality controller should work
- Test mode should generate sample outputs

### 9. Check Output Files
After running tests, verify outputs are created:
```bash
ls -la output/
ls -la logs/
```

## Troubleshooting Common Issues

### Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Permission Issues
```bash
# Fix directory permissions
chmod 755 logs output
```

### API Key Issues
- Verify all required API keys are in .env file
- Check that .env file is in the project root directory
- Ensure no extra spaces or quotes around API keys

### Python Version Issues
```bash
# Check Python version (should be 3.8+)
python3 --version

# If needed, install specific version
sudo apt install python3.9 python3.9-venv python3.9-pip
```

## Success Criteria
✅ All system tests pass  
✅ Virtual environment is active  
✅ Dependencies are installed  
✅ .env file contains valid API keys  
✅ Test mode generates sample outputs  
✅ Logs directory is writable  

## Next Phase (After Setup)
Once setup is complete, the system can be run in:
- **Test mode**: `python main.py --test`
- **Production mode**: `python main.py`

## Files to Monitor
- `logs/market_voices.log` - System logs
- `output/` - Generated scripts and data
- `.env` - Configuration (never commit to git)

## Important Notes
- Never commit .env files to version control
- Always activate virtual environment before running: `source venv/bin/activate`
- Test mode uses mock data and doesn't require real API calls
- Production mode requires valid API keys and internet connection

---

**Ready to proceed with setup? Start with Step 1 and report progress after each step.** 