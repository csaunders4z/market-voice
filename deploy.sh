#!/bin/bash

# Market Voices Production Deployment Script
# This script automates the deployment process for the Market Voices system

set -e  # Exit on any error

# Configuration
APP_NAME="market-voices"
APP_DIR="/opt/market-voices"
SERVICE_NAME="market-voices"
USER_NAME="market-voices"
BACKUP_DIR="/opt/backups"
LOG_FILE="/var/log/market-voices-deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root. Please run as a regular user with sudo privileges."
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$PYTHON_VERSION >= 3.9" | bc -l) -eq 0 ]]; then
        error "Python 3.9 or higher is required. Current version: $PYTHON_VERSION"
    fi
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        error "Git is not installed"
    fi
    
    # Check if systemd is available
    if ! command -v systemctl &> /dev/null; then
        error "Systemd is not available"
    fi
    
    success "System requirements check passed"
}

# Create application user
create_user() {
    log "Creating application user..."
    
    if ! id "$USER_NAME" &>/dev/null; then
        sudo useradd -r -s /bin/bash -d "$APP_DIR" "$USER_NAME"
        success "Created user: $USER_NAME"
    else
        warning "User $USER_NAME already exists"
    fi
}

# Create application directory
create_directories() {
    log "Creating application directories..."
    
    sudo mkdir -p "$APP_DIR"
    sudo mkdir -p "$BACKUP_DIR"
    sudo mkdir -p "/var/log/$APP_NAME"
    sudo mkdir -p "/etc/$APP_NAME"
    
    sudo chown -R "$USER_NAME:$USER_NAME" "$APP_DIR"
    sudo chown -R "$USER_NAME:$USER_NAME" "$BACKUP_DIR"
    sudo chown -R "$USER_NAME:$USER_NAME" "/var/log/$APP_NAME"
    sudo chown -R "$USER_NAME:$USER_NAME" "/etc/$APP_NAME"
    
    success "Created application directories"
}

# Backup current installation
backup_current() {
    if [[ -d "$APP_DIR" && "$(ls -A $APP_DIR)" ]]; then
        log "Creating backup of current installation..."
        
        BACKUP_NAME="$BACKUP_DIR/${APP_NAME}-backup-$(date +%Y%m%d_%H%M%S).tar.gz"
        sudo tar -czf "$BACKUP_NAME" -C "$APP_DIR" .
        
        success "Backup created: $BACKUP_NAME"
    else
        warning "No existing installation to backup"
    fi
}

# Clone or update repository
update_code() {
    log "Updating application code..."
    
    if [[ -d "$APP_DIR/.git" ]]; then
        # Update existing repository
        cd "$APP_DIR"
        sudo -u "$USER_NAME" git fetch origin
        sudo -u "$USER_NAME" git reset --hard origin/main
        success "Updated existing repository"
    else
        # Clone new repository
        sudo -u "$USER_NAME" git clone https://github.com/csaunders4z/market-voice.git "$APP_DIR"
        success "Cloned new repository"
    fi
}

# Install Python dependencies
install_dependencies() {
    log "Installing Python dependencies..."
    
    cd "$APP_DIR"
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        sudo -u "$USER_NAME" python3 -m venv venv
        success "Created virtual environment"
    fi
    
    # Activate virtual environment and install dependencies
    sudo -u "$USER_NAME" ./venv/bin/pip install --upgrade pip
    sudo -u "$USER_NAME" ./venv/bin/pip install -r requirements.txt
    
    success "Installed Python dependencies"
}

# Create systemd service
create_service() {
    log "Creating systemd service..."
    
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Market Voices Financial News System
After=network.target

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    
    success "Created systemd service: $SERVICE_NAME"
}

# Configure environment variables
configure_environment() {
    log "Configuring environment variables..."
    
    ENV_FILE="/etc/$APP_NAME/.env"
    
    # Create environment file template
    sudo -u "$USER_NAME" tee "$ENV_FILE" > /dev/null <<EOF
# Market Voices Production Configuration
# Update these values with your actual API keys

# API Keys (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
FMP_API_KEY=your_fmp_api_key_here
FINNHUB_API_KEY=your_finnhub_api_key_here

THE_NEWS_API_API_KEY=your_the_news_api_key_here
NEWSAPI_API_KEY=your_newsapi_api_key_here
NEWSDATA_IO_API_KEY=your_newsdata_io_api_key_here
BIZTOC_API_KEY=your_biztoc_api_key_here

# Optional API Keys
RAPIDAPI_KEY=your_rapidapi_key_here

# Budget Configuration
MONTHLY_BUDGET=50.0
BUDGET_WARNING_THRESHOLD=0.8
BUDGET_CRITICAL_THRESHOLD=0.95
BUDGET_ALERT_EMAIL=admin@yourdomain.com

# Application Settings
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///market_voices.db
OUTPUT_DIRECTORY=output
EOF
    
    warning "Please update the environment file at $ENV_FILE with your actual API keys"
    success "Created environment configuration"
}

# Run tests
run_tests() {
    log "Running application tests..."
    
    cd "$APP_DIR"
    
    # Run basic tests
    if sudo -u "$USER_NAME" ./venv/bin/python -m pytest tests/ -v; then
        success "Tests passed"
    else
        error "Tests failed"
    fi
}

# Start application
start_application() {
    log "Starting application..."
    
    sudo systemctl start "$SERVICE_NAME"
    sleep 5
    
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        success "Application started successfully"
    else
        error "Failed to start application"
    fi
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Wait for application to be ready
    sleep 10
    
    # Check if service is running
    if ! sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        error "Service is not running"
    fi
    
    # Check service status
    sudo systemctl status "$SERVICE_NAME" --no-pager
    
    # Check logs for errors
    if sudo journalctl -u "$SERVICE_NAME" --since "5 minutes ago" | grep -i error; then
        warning "Found errors in recent logs"
    else
        success "No errors found in recent logs"
    fi
    
    success "Health check completed"
}

# Configure logging
configure_logging() {
    log "Configuring logging..."
    
    # Create logrotate configuration
    sudo tee "/etc/logrotate.d/$APP_NAME" > /dev/null <<EOF
/var/log/$APP_NAME/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER_NAME $USER_NAME
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF
    
    success "Configured log rotation"
}

# Display deployment summary
deployment_summary() {
    echo
    echo "=========================================="
    echo "           DEPLOYMENT SUMMARY"
    echo "=========================================="
    echo "Application: $APP_NAME"
    echo "Directory: $APP_DIR"
    echo "Service: $SERVICE_NAME"
    echo "User: $USER_NAME"
    echo "Log File: $LOG_FILE"
    echo
    echo "Next Steps:"
    echo "1. Update API keys in /etc/$APP_NAME/.env"
    echo "2. Configure your domain and SSL certificate"
    echo "3. Set up monitoring and alerting"
    echo "4. Test the application thoroughly"
    echo
    echo "Useful Commands:"
    echo "  Check status: sudo systemctl status $SERVICE_NAME"
    echo "  View logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "  Restart: sudo systemctl restart $SERVICE_NAME"
    echo "  Stop: sudo systemctl stop $SERVICE_NAME"
    echo
}

# Main deployment function
main() {
    log "Starting Market Voices deployment..."
    
    check_root
    check_requirements
    create_user
    create_directories
    backup_current
    update_code
    install_dependencies
    create_service
    configure_environment
    run_tests
    start_application
    health_check
    configure_logging
    deployment_summary
    
    success "Deployment completed successfully!"
}

# Run main function
main "$@"  