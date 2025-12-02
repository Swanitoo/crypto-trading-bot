#!/bin/bash

# Crypto Trading Bot - Setup Script
# This script sets up the environment and dependencies

set -e  # Exit on error

echo "=========================================="
echo "🤖 Crypto Trading Bot - Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Create virtual environment
echo ""
echo "🔧 Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment already exists. Skipping.${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✅ Pip upgraded${NC}"

# Install dependencies
echo ""
echo "📚 Installing dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p data
mkdir -p logs
echo -e "${GREEN}✅ Directories created${NC}"

# Setup .env file
echo ""
echo "⚙️  Setting up configuration..."
if [ ! -f "config/.env" ]; then
    cp config/.env.example config/.env
    echo -e "${GREEN}✅ .env file created from example${NC}"
    echo -e "${YELLOW}⚠️  Please edit config/.env and add your API keys${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists. Skipping.${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Edit your API keys:"
echo -e "   ${YELLOW}nano config/.env${NC}"
echo ""
echo "2. Add your OpenAI API key (REQUIRED):"
echo -e "   ${YELLOW}OPENAI_API_KEY=sk-your-key-here${NC}"
echo ""
echo "3. (Optional) Add Binance keys for live trading:"
echo -e "   ${YELLOW}BINANCE_API_KEY=your-key${NC}"
echo -e "   ${YELLOW}BINANCE_API_SECRET=your-secret${NC}"
echo ""
echo "4. Start the bot:"
echo -e "   ${GREEN}source venv/bin/activate${NC}"
echo -e "   ${GREEN}python main.py${NC}"
echo ""
echo "5. Open dashboard in browser:"
echo -e "   ${GREEN}http://localhost:5000${NC}"
echo ""
echo -e "${YELLOW}💡 Tip: Start in PAPER TRADING mode first!${NC}"
echo ""
