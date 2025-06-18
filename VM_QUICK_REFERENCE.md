# Ubuntu VM Quick Reference

## Download Links
- **VirtualBox**: https://www.virtualbox.org/wiki/Downloads
- **Ubuntu Desktop**: https://ubuntu.com/download/desktop

## VM Settings (Recommended)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB minimum
- **CPU**: 2 cores minimum
- **Network**: NAT (default)

## Quick Commands

### After Ubuntu Installation:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install tools
sudo apt install python3 python3-pip python3-venv git curl wget nano -y

# Run setup script
chmod +x setup_ubuntu.sh
./setup_ubuntu.sh
```

### Project Setup:
```bash
# Clone repo (update URL)
git clone https://github.com/yourusername/stock-voice.git
cd stock-voice

# Create environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp config.env.example .env
nano .env  # Add your API keys
```

### Common Commands:
```bash
# Activate environment
source venv/bin/activate

# Run tests
python test_enhanced_system.py

# Run main system
python main.py --mode test

# Deactivate environment
deactivate
```

## API Keys Needed
- ALPHA_VANTAGE_API_KEY
- NEWS_API_KEY  
- OPENAI_API_KEY
- BIZTOC_API_KEY
- FMP_API_KEY

## Troubleshooting
- **Permission denied**: Use `sudo`
- **Python not found**: Use `python3`
- **Network issues**: Check VM network settings
- **Slow performance**: Increase RAM allocation

## Security Notes
- Never commit .env files
- Use strong VM passwords
- Keep Ubuntu updated
- Backup your work regularly 