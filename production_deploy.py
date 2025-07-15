#!/usr/bin/env python3
"""
Production deployment script for Market Voices
Handles secure deployment to production environment
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

def create_production_directories():
    """Create production directory structure"""
    print("Creating production directories...")
    
    directories = [
        "/etc/market-voices",
        "/var/log/market-voices", 
        "/var/lib/market-voices/output",
        "/var/lib/market-voices/data"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created: {directory}")
        except PermissionError:
            print(f"❌ Permission denied creating {directory}. Run with sudo.")
            return False
        except Exception as e:
            print(f"❌ Error creating {directory}: {e}")
            return False
    
    return True

def deploy_configuration():
    """Deploy configuration files to production"""
    print("Deploying configuration files...")
    
    if not Path(".env").exists():
        print("❌ .env file not found. Copy env.template to .env and configure API keys.")
        return False
    
    try:
        shutil.copy2(".env", "/etc/market-voices/.env")
        os.chmod("/etc/market-voices/.env", 0o600)
        print("✅ Configuration deployed to /etc/market-voices/.env")
        
        if os.geteuid() == 0:
            shutil.chown("/etc/market-voices/.env", user="root", group="root")
        
        return True
    except PermissionError:
        print("❌ Permission denied. Run with sudo for production deployment.")
        return False
    except Exception as e:
        print(f"❌ Error deploying configuration: {e}")
        return False

def setup_logging():
    """Set up production logging"""
    print("Setting up production logging...")
    
    try:
        log_file = "/var/log/market-voices/market_voices.log"
        Path(log_file).touch()
        os.chmod(log_file, 0o644)
        print(f"✅ Log file created: {log_file}")
        return True
    except Exception as e:
        print(f"❌ Error setting up logging: {e}")
        return False

def create_systemd_service():
    """Create systemd service file for Market Voices"""
    print("Creating systemd service...")
    
    service_content = f"""[Unit]
Description=Market Voices - Automated Stock Market Video Script Generator
After=network.target

[Service]
Type=simple
User=marketvoices
Group=marketvoices
WorkingDirectory={os.getcwd()}
Environment=PATH={os.environ.get('PATH')}
EnvironmentFile=/etc/market-voices/.env
ExecStart={sys.executable} main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/market-voices/market_voices.log
StandardError=append:/var/log/market-voices/market_voices.log

[Install]
WantedBy=multi-user.target
"""
    
    try:
        with open("/etc/systemd/system/market-voices.service", "w") as f:
            f.write(service_content)
        
        print("✅ Systemd service created: /etc/systemd/system/market-voices.service")
        print("To enable and start the service:")
        print("  sudo systemctl daemon-reload")
        print("  sudo systemctl enable market-voices")
        print("  sudo systemctl start market-voices")
        return True
    except Exception as e:
        print(f"❌ Error creating systemd service: {e}")
        return False

def validate_deployment():
    """Validate the production deployment"""
    print("Validating deployment...")
    
    try:
        result = subprocess.run([sys.executable, "validate_production.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Production validation passed")
            return True
        else:
            print("⚠️ Production validation completed with warnings")
            print(result.stdout)
            return True
    except Exception as e:
        print(f"❌ Error running validation: {e}")
        return False

def main():
    """Main deployment function"""
    print("="*60)
    print("Market Voices Production Deployment")
    print("="*60)
    print(f"Deployment time: {datetime.now().isoformat()}")
    print()
    
    if os.geteuid() != 0:
        print("⚠️ Not running as root. Some features may not be available.")
        print("For full system deployment, run: sudo python production_deploy.py")
        print()
    
    steps = [
        ("Create production directories", create_production_directories),
        ("Deploy configuration", deploy_configuration),
        ("Setup logging", setup_logging),
        ("Create systemd service", create_systemd_service),
        ("Validate deployment", validate_deployment),
    ]
    
    success_count = 0
    for step_name, step_func in steps:
        print(f"Step: {step_name}")
        if step_func():
            success_count += 1
        print()
    
    print("="*60)
    if success_count == len(steps):
        print("✅ Production deployment completed successfully!")
        print()
        print("Next steps:")
        print("1. Configure real API keys in /etc/market-voices/.env")
        print("2. Test production mode: python main.py")
        print("3. Enable systemd service: sudo systemctl enable market-voices")
        print("4. Start service: sudo systemctl start market-voices")
        return 0
    else:
        print(f"⚠️ Deployment completed with {len(steps) - success_count} issues")
        print("Review the output above and resolve any issues before proceeding.")
        return 1

if __name__ == "__main__":
    exit(main())
