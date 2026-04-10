#!/bin/bash

set -e

echo "=== MarketingAgents Full Stack EC2 Setup ==="

# Update system
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# Install Node.js 20.x
echo "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install dependencies
echo "Installing dependencies..."
sudo apt install -y python3.12-venv python3-pip nginx certbot python3-certbot-nginx

# Install PM2 for process management
echo "Installing PM2..."
sudo npm install -g pm2

# Setup Backend
echo "Setting up Backend..."
cd /home/ubuntu/MarketingAgents/backend
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "python-jose[cryptography]" "passlib[bcrypt]" psycopg2-binary bcrypt python-multipart slowapi httpx email-validator
pip install -r requirements.txt

# Setup Frontend
echo "Setting up Frontend..."
cd /home/ubuntu/MarketingAgents/frontend
npm install --legacy-peer-deps
npm run build

# Configure PM2 for Frontend
echo "Configuring PM2..."
cd /home/ubuntu/MarketingAgents/frontend
pm2 stop all 2>/dev/null || true
pm2 delete all 2>/dev/null || true
pm2 start npm --name "frontend" -- start

# Save PM2 config
pm2 save
pm2 startup

# Setup Backend as systemd service
echo "Setting up Backend service..."
sudo cp /home/ubuntu/MarketingAgents/deploy/marketingagents.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable marketingagents
sudo systemctl start marketingagents

# Setup Nginx for both services
echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/marketingagents > /dev/null <<EOF
upstream frontend {
    server 127.0.0.1:3000;
}

upstream backend {
    server 127.0.0.1:8501;
}

server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }

    # Backend (Streamlit)
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_read_timeout 86400;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/marketingagents /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

echo "=== Setup Complete ==="
echo ""
echo "Services:"
echo "  Frontend (Next.js): http://localhost:3000"
echo "  Backend (Streamlit): http://localhost:8501"
echo "  Nginx: Port 80"
echo ""
echo "Check status:"
echo "  pm2 status"
echo "  sudo systemctl status marketingagents"
echo "  sudo systemctl status nginx"
