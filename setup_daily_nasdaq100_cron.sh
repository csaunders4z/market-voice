#!/bin/bash
# Setup daily NASDAQ-100 symbol update cron job for Market Voices

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Market Voices - Daily NASDAQ-100 Update${NC}"
echo -e "${BLUE}  Cron Job Setup Script${NC}"
echo -e "${BLUE}========================================${NC}"

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${YELLOW}Current directory: ${SCRIPT_DIR}${NC}"

# Check if we're in the right directory
if [[ ! -f "daily_nasdaq100_update.py" ]]; then
    echo -e "${RED}Error: daily_nasdaq100_update.py not found in current directory${NC}"
    echo -e "${YELLOW}Please run this script from the market-voice project root${NC}"
    exit 1
fi

# Get Python path
PYTHON_PATH=$(which python3)
if [[ -z "$PYTHON_PATH" ]]; then
    echo -e "${RED}Error: python3 not found in PATH${NC}"
    exit 1
fi

echo -e "${GREEN}Python path: ${PYTHON_PATH}${NC}"

# Create the cron job command
CRON_CMD="0 6 * * * cd ${SCRIPT_DIR} && ${PYTHON_PATH} daily_nasdaq100_update.py >> logs/cron_nasdaq100_update.log 2>&1"

echo -e "${YELLOW}Proposed cron job:${NC}"
echo -e "${BLUE}${CRON_CMD}${NC}"
echo ""

# Ask for confirmation
read -p "Do you want to add this cron job? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create temporary file with current crontab
    TEMP_CRON=$(mktemp)
    crontab -l > "$TEMP_CRON" 2>/dev/null || true
    
    # Check if cron job already exists
    if grep -q "daily_nasdaq100_update.py" "$TEMP_CRON"; then
        echo -e "${YELLOW}Warning: A cron job for daily_nasdaq100_update.py already exists${NC}"
        echo -e "${YELLOW}Current crontab entries:${NC}"
        grep "daily_nasdaq100_update.py" "$TEMP_CRON"
        echo ""
        read -p "Do you want to replace the existing cron job? (y/N): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Remove existing cron job
            sed -i '/daily_nasdaq100_update.py/d' "$TEMP_CRON"
        else
            echo -e "${YELLOW}Cron job setup cancelled${NC}"
            rm "$TEMP_CRON"
            exit 0
        fi
    fi
    
    # Add new cron job
    echo "$CRON_CMD" >> "$TEMP_CRON"
    
    # Install the new crontab
    crontab "$TEMP_CRON"
    rm "$TEMP_CRON"
    
    echo -e "${GREEN}✅ Cron job added successfully!${NC}"
    echo -e "${BLUE}The NASDAQ-100 symbols will be updated daily at 6:00 AM${NC}"
    echo ""
    echo -e "${YELLOW}To view current crontab:${NC}"
    echo -e "${BLUE}  crontab -l${NC}"
    echo ""
    echo -e "${YELLOW}To remove the cron job:${NC}"
    echo -e "${BLUE}  crontab -e${NC}"
    echo ""
    echo -e "${YELLOW}To view cron logs:${NC}"
    echo -e "${BLUE}  tail -f logs/cron_nasdaq100_update.log${NC}"
    
else
    echo -e "${YELLOW}Cron job setup cancelled${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Setup Complete${NC}"
echo -e "${BLUE}========================================${NC}" 