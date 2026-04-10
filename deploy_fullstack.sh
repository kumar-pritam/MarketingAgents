#!/bin/bash

set -e

echo "=== Marketing Agents Full Stack Deployment ==="
echo ""

GREEN='\033[0;32m'
NC='\033[0m'

# Clean up first
echo -e "${GREEN}[1/7] Cleaning up...${NC}"
sudo docker system prune -af --volumes 2>/dev/null || true

# Update and install Docker
echo -e "${GREEN}[2/7] Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    sudo apt update && sudo apt install -y docker.io docker-compose
fi
sudo systemctl start docker 2>/dev/null || true

# Get code
echo -e "${GREEN}[3/7] Getting code...${NC}"
if [ -d "MarketingAgents" ]; then
    cd MarketingAgents
    git pull origin main
else
    git clone https://github.com/kumar-pritam/MarketingAgents.git
    cd MarketingAgents
fi

# Setup env
echo -e "${GREEN}[4/7] Environment...${NC}"
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
fi

# Build backend only
echo -e "${GREEN}[5/7] Building Backend...${NC}"
sudo docker build -t ma-backend ./backend

# Clean before frontend
sudo docker image prune -af --filter "until=5m" 2>/dev/null || true

# Build frontend
echo -e "${GREEN}[6/7] Building Frontend...${NC}"
sudo docker build -t ma-frontend ./frontend

# Clean before running
sudo docker image prune -af --filter "until=5m" 2>/dev/null || true

# Run all
echo -e "${GREEN}[7/7] Starting services...${NC}"
sudo docker-compose -f docker-compose.fullstack.yml up -d

echo ""
echo -e "${GREEN}=== Done! ===${NC}"
echo "Access at: http://13.232.143.135"
echo ""
echo "Logs: docker-compose -f docker-compose.fullstack.yml logs -f"