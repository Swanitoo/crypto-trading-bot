#!/bin/bash

# Script pour voir le statut du bot

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   Crypto Trading Bot - Status${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Vérifier le PID
if [ -f ".bot.pid" ]; then
    PID=$(cat .bot.pid)

    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Bot is RUNNING${NC}"
        echo -e "   PID: $PID"
        echo -e "   Dashboard: ${CYAN}http://localhost:5000${NC}"
        echo ""

        # Afficher les dernières lignes du log
        echo -e "${CYAN}📊 Recent activity:${NC}"
        echo ""
        tail -10 bot.log | grep -E "(INFO|WARNING|ERROR)" | sed 's/^/   /'
        echo ""
        echo -e "${YELLOW}💡 Commands:${NC}"
        echo -e "   View logs: ${CYAN}tail -f bot.log${NC}"
        echo -e "   Stop bot:  ${CYAN}./stop_bot.sh${NC}"
    else
        echo -e "${RED}❌ Bot is NOT running (stale PID file)${NC}"
        echo -e "   Removing stale PID file..."
        rm .bot.pid
    fi
else
    echo -e "${YELLOW}⚠️  Bot is NOT running${NC}"
    echo ""
    echo -e "${YELLOW}💡 To start the bot:${NC}"
    echo -e "   ${CYAN}./run_bot.sh${NC}"
fi

echo ""
