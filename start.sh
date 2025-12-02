#!/bin/bash

# Quick start script for Crypto Trading Bot

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo -e "${YELLOW}Please run ./setup.sh first${NC}"
    exit 1
fi

# Check if .env exists
if [ ! -f "config/.env" ]; then
    echo -e "${RED}❌ Configuration file not found!${NC}"
    echo -e "${YELLOW}Please run ./setup.sh and configure config/.env${NC}"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start the bot
echo -e "${GREEN}🚀 Starting Crypto Trading Bot...${NC}"
echo ""
python main.py "$@"
