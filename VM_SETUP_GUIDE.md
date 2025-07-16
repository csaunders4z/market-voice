# Ubuntu VM Setup Guide for Market Voices

## Prerequisites
- VirtualBox (latest version)
- At least 8GB RAM available for VM
- 20GB free disk space
- Internet connection

## Step 1: Download Ubuntu Desktop
1. Go to https://ubuntu.com/download/desktop
2. Download Ubuntu 22.04.3 LTS (Long Term Support)
3. Choose the 64-bit version

## Step 2: Create Virtual Machine in VirtualBox
1. Open VirtualBox
2. Click "New" to create a new VM
3. Configure settings:
   - **Name**: Market Voices Dev
   - **Type**: Linux
   - **Version**: Ubuntu (64-bit)
   - **Memory**: 4096 MB (4GB minimum, 8GB recommended)
   - **Hard disk**: Create a virtual hard disk now
   - **Hard disk file type**: VDI
   - **Storage on physical hard disk**: Dynamically allocated
   - **File location and size**: 20GB minimum

## Step 3: Install Ubuntu
1. Start the VM
2. Select "Install Ubuntu"
3. Choose "Normal installation" with "Download updates while installing"
4. Choose "Erase disk and install Ubuntu" (this only affects the virtual disk)
5. Set timezone and create user account
6. Wait for installation to complete (15-30 minutes)
7. Restart when prompted

## Step 4: Install Guest Additions (Optional but Recommended)
1. In the VM, go to Devices > Insert Guest Additions CD Image
2. Open terminal and run:
   ```bash
   sudo apt update
   sudo apt install build-essential dkms
   cd /media/[username]/VBox_GAs_[version]
   sudo ./VBoxLinuxAdditions.run
   ```
3. Restart VM

## Step 5: Install Python and Development Tools
1. Open terminal and run:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   sudo apt install python3 python3-pip python3-venv git curl wget -y
   ```

## Step 6: Clone Your Project
1. Create a development directory:
   ```bash
   mkdir ~/projects
   cd ~/projects
   ```

2. Clone your GitHub repository:
   ```bash
   git clone https://github.com/[your-username]/stock-voice.git
   cd stock-voice
   ```

## Step 7: Set Up Python Environment
1. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Step 8: Configure Environment Variables
1. Create .env file safely:
   ```bash
   # Check if .env already exists first
   ls -la .env
   
   # If .env exists and contains real API keys, back it up first:
   # mkdir -p backups && cp .env backups/.env.backup.$(date +%Y%m%d_%H%M%S)
   
   # Only copy template if no real keys exist:
   cp config.env.example .env
   ```

2. Edit .env file with your API keys:
   ```bash
   nano .env
   ```

3. Add your API keys (get from your secure storage):
   ```
   ALPHA_VANTAGE_API_KEY=your_key_here
   NEWS_API_KEY=your_key_here
   OPENAI_API_KEY=your_key_here
   BIZTOC_API_KEY=your_key_here
   FMP_API_KEY=your_key_here
   ```

## Step 9: Test the Setup
1. Run a quick test:
   ```bash
   python test_enhanced_system.py
   ```

2. Test the main system:
   ```bash
   python main.py --mode test
   ```

## Step 10: Set Up Development Tools (Optional)
1. Install VS Code:
   ```bash
   sudo snap install code --classic
   ```

2. Install useful VS Code extensions:
   - Python
   - GitLens
   - Python Docstring Generator
   - Python Test Explorer

## Step 11: Configure Git
1. Set up your Git identity:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

2. Set up SSH key for GitHub (optional but recommended):
   ```bash
   ssh-keygen -t ed25519 -C "your.email@example.com"
   cat ~/.ssh/id_ed25519.pub
   ```
   Copy the output and add to GitHub SSH keys

## Troubleshooting

### Common Issues:
1. **VM is slow**: Increase RAM allocation in VM settings
2. **Network issues**: Check VM network adapter settings
3. **Permission errors**: Use `sudo` for system-level operations
4. **Python not found**: Ensure you're using `python3` command

### Performance Tips:
1. Enable 3D acceleration in VM settings
2. Allocate more RAM if available
3. Use SSD storage if possible
4. Enable nested virtualization if supported

## Next Steps
1. Test all API connections
2. Run the complete workflow
3. Set up automated testing
4. Configure CI/CD pipeline
5. Deploy to cloud environment

## Security Notes
- Never commit .env files to Git
- Use strong passwords for VM user account
- Keep Ubuntu updated regularly
- Consider using a VPN for additional security

## Backup Strategy
1. Export VM as OVA file periodically
2. Use Git for code version control
3. Backup .env file securely
4. Document any custom configurations  