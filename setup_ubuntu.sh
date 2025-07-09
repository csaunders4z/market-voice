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

# Create .env file
echo "🔐 Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp config.env.example .env
    echo "✅ Created .env file from template"
    echo "⚠️  Please edit .env file with your API keys:"
    echo "   nano .env"
else
    echo "✅ .env file already exists"
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
