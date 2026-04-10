#!/bin/bash

set -e

echo "=== Marketing Agents Full Stack Deployment ==="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}[1/5] Updating system...${NC}"
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose curl

# Step 2: Install Docker if not present
if ! command -v docker &> /dev/null; then
    sudo systemctl start docker
    sudo systemctl enable docker
fi

# Step 3: Clone/pull repo
echo -e "${GREEN}[2/5] Updating code...${NC}"
if [ -d "MarketingAgents" ]; then
    cd MarketingAgents
    git pull origin main
else
    git clone https://github.com/kumar-pritam/MarketingAgents.git
    cd MarketingAgents
fi

# Step 4: Setup environment
echo -e "${GREEN}[3/5] Setting up environment...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
    fi
fi

# Step 5: Build and run
echo -e "${GREEN}[4/5] Building containers...${NC}"
sudo docker-compose -f docker-compose.fullstack.yml down -v
sudo docker-compose -f docker-compose.fullstack.yml up -d --build

# Step 6: Verify
echo -e "${GREEN}[5/5] Verifying deployment...${NC}"
sleep 10
sudo docker ps

echo ""
echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo ""
echo "Access at: http://<YOUR_EC2_IP>"
echo "Backend API: http://<YOUR_EC2_IP>/api/v1"
echo ""
echo "Commands:"
echo "  docker-compose -f docker-compose.fullstack.yml logs -f"
echo "  docker-compose -f docker-compose.fullstack.yml restart"