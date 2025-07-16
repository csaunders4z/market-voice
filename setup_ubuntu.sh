#!/bin/bash

# Market Voices Ubuntu VM Setup Script
# Run this script after installing Ubuntu in your VM

echo "🚀 Setting up Market Voices development environment..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "🔧 Installing development tools..."
sudo apt install python3 python3-pip python3-venv git curl wget nano -y

# Create projects directory
echo "📁 Creating projects directory..."
mkdir -p ~/projects
cd ~/projects

# Clone repository (you'll need to update the URL)
echo "📥 Cloning repository..."
if [ ! -d "market-voice" ]; then
    echo "Please update the git clone URL in this script with your actual repository URL"
    echo "Example: git clone https://github.com/yourusername/stock-voice.git"
    # git clone https://github.com/csaunders4z/market-voice.git
else
    echo "Repository already exists"
fi

cd market-voice

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

has_real_api_keys() {
    local env_file="$1"
    
    if [[ ! -f "$env_file" ]]; then
        return 1
    fi
    
    if grep -q "your_.*_api_key_here\|your_.*_key_here\|INSERT_.*_HERE\|REPLACE_.*_HERE" "$env_file"; then
        return 1
    fi
    
    local has_keys=false
    while IFS='=' read -r key value; do
        [[ "$key" =~ ^[[:space:]]*# ]] && continue
        [[ -z "$key" ]] && continue
        
        if [[ "$key" =~ API_KEY$ ]] && [[ -n "$value" ]] && [[ "$value" != "your_"*"_here" ]]; then
            has_keys=true
            break
        fi
    done < "$env_file"
    
    if $has_keys; then
        return 0
    else
        return 1
    fi
}

# Create .env file with protection
echo "🔐 Setting up environment variables..."
if [ -f ".env" ]; then
    if has_real_api_keys ".env"; then
        echo "🚨 CRITICAL: .env file contains real API keys!"
        echo "This operation will overwrite your existing API keys."
        echo ""
        read -p "Create backup before proceeding? (STRONGLY RECOMMENDED) (y/n): " backup
        if [[ "$backup" == "y" || "$backup" == "Y" ]]; then
            timestamp=$(date +%Y%m%d_%H%M%S)
            mkdir -p backups
            cp ".env" "backups/.env.backup.$timestamp"
            echo "✅ Backup created: backups/.env.backup.$timestamp"
        else
            echo "⚠️  No backup created - your API keys will be lost!"
        fi
        
        echo ""
        read -p "Are you SURE you want to overwrite .env with template? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            echo "❌ Operation cancelled to protect your API keys"
            exit 1
        fi
    else
        echo "⚠️  .env file already exists (contains template content)"
        read -p "Do you want to create a backup first? (y/n): " backup
        if [[ "$backup" == "y" || "$backup" == "Y" ]]; then
            timestamp=$(date +%Y%m%d_%H%M%S)
            mkdir -p backups
            cp ".env" "backups/.env.backup.$timestamp"
            echo "✅ Backup created: backups/.env.backup.$timestamp"
        fi
    fi
fi

if [ ! -f ".env" ] || [[ "$confirm" == "yes" ]]; then
    cp config.env.example .env
    echo "✅ Created .env file from template"
    echo "⚠️  Please edit .env file with your API keys:"
    echo "   nano .env"
else
    echo "✅ .env file already exists"
    echo "   Please verify your API keys are configured"
fi

# Create logs directory
echo "📝 Creating logs directory..."
mkdir -p logs
mkdir -p output

# Set up Git configuration
echo "🔧 Setting up Git configuration..."
echo "Please configure Git with your details:"
echo "git config --global user.name 'Your Name'"
echo "git config --global user.email 'your.email@example.com'"

# Install VS Code (optional)
echo "💻 Installing VS Code..."
sudo snap install code --classic

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys: nano .env"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Test the system: python test_enhanced_system.py"
echo "4. Run main system: python main.py --mode test"
echo ""
echo "Happy coding! 🚀"  
