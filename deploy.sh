#!/bin/bash

set -e

echo "=== Marketing Agents Deployment Script ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Warning: Running as root. It's recommended to run as ubuntu user.${NC}"
fi

# Step 1: Update system
echo -e "${GREEN}[1/6] Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Step 2: Install Docker if not present
echo -e "${GREEN}[2/6] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    sudo apt install -y docker.io docker-compose
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo -e "${YELLOW}Docker installed. You may need to logout/login for group changes to take effect.${NC}"
else
    echo "Docker already installed."
fi

# Step 3: Clone repository
echo -e "${GREEN}[3/6] Cloning repository...${NC}"
if [ -d "MarketingAgents" ]; then
    echo "Directory MarketingAgents already exists. Pulling latest..."
    cd MarketingAgents
    git pull origin main
else
    git clone https://github.com/kumar-pritam/MarketingAgents.git
    cd MarketingAgents
fi

# Step 4: Setup environment
echo -e "${GREEN}[4/6] Setting up environment...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}Created .env from .env.example. Please edit it with your API keys!${NC}"
    else
        echo "OPENROUTER_API_KEY=" > .env
        echo -e "${YELLOW}Created empty .env. Please add your API keys!${NC}"
    fi
else
    echo ".env already exists."
fi

# Step 5: Build and run Docker
echo -e "${GREEN}[5/6] Building and starting Docker container...${NC}"
sudo docker-compose down -v
sudo docker system prune -a --volumes -f
sudo docker-compose up -d --build

# Step 6: Verify deployment
echo -e "${GREEN}[6/6] Verifying deployment...${NC}"
sleep 5
sudo docker ps

echo ""
echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo ""
echo "Access the application at: http://<YOUR_EC2_IP>:8501"
echo ""
echo "Useful commands:"
echo "  docker-compose logs -f    # View logs"
echo "  docker-compose restart    # Restart app"
echo "  docker-compose stop       # Stop app"
echo "  docker-compose up -d      # Rebuild and start"