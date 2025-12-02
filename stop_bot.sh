#!/bin/bash

# Script pour arrêter le bot

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ ! -f ".bot.pid" ]; then
    echo -e "${YELLOW}⚠️  Bot is not running (no PID file found)${NC}"
    exit 1
fi

PID=$(cat .bot.pid)

if ! ps -p $PID > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Bot process (PID $PID) is not running${NC}"
    rm .bot.pid
    exit 1
fi

echo -e "${YELLOW}🛑 Stopping bot (PID $PID)...${NC}"
kill $PID

# Attendre que le processus se termine
sleep 2

if ps -p $PID > /dev/null 2>&1; then
    echo -e "${RED}⚠️  Process still running, forcing kill...${NC}"
    kill -9 $PID
    sleep 1
fi

if ! ps -p $PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Bot stopped successfully${NC}"
    rm .bot.pid
else
    echo -e "${RED}❌ Failed to stop bot${NC}"
    exit 1
fi
