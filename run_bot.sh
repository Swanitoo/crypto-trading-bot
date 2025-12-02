#!/bin/bash

# Script pour lancer le bot en arrière-plan

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Vérifier si le bot tourne déjà
if [ -f ".bot.pid" ]; then
    PID=$(cat .bot.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Bot already running with PID $PID${NC}"
        echo -e "${YELLOW}Use ./stop_bot.sh to stop it first${NC}"
        exit 1
    else
        rm .bot.pid
    fi
fi

# Activer l'environnement virtuel
source venv/bin/activate

# Lancer le bot en arrière-plan
echo -e "${GREEN}🚀 Starting Crypto Trading Bot...${NC}"
nohup python main.py > bot.log 2>&1 &
BOT_PID=$!

# Sauvegarder le PID
echo $BOT_PID > .bot.pid

# Attendre que le serveur démarre
sleep 3

# Vérifier que le bot tourne
if ps -p $BOT_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Bot started successfully!${NC}"
    echo -e "${GREEN}   PID: $BOT_PID${NC}"
    echo -e "${GREEN}   Dashboard: http://localhost:5000${NC}"
    echo -e "${GREEN}   Logs: tail -f bot.log${NC}"
    echo ""
    echo -e "${YELLOW}💡 To stop the bot: ./stop_bot.sh${NC}"
else
    echo -e "${RED}❌ Failed to start bot${NC}"
    echo -e "${YELLOW}Check bot.log for errors${NC}"
    rm .bot.pid
    exit 1
fi
