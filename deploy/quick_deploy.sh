#!/bin/bash

set -e

echo "=== Quick Deploy (Dev Mode) ==="

cd /home/ubuntu/MarketingAgents

# Pull latest code
echo "Pulling latest code..."
git pull origin main

# Setup Backend
echo "Setting up Backend..."
cd /home/ubuntu/MarketingAgents/backend
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "python-jose[cryptography]" "passlib[bcrypt]" psycopg2-binary bcrypt python-multipart slowapi httpx email-validator
pip install -r requirements.txt

# Setup Frontend (dev mode - no build needed)
echo "Setting up Frontend..."
cd /home/ubuntu/MarketingAgents/frontend
npm install --legacy-peer-deps

# Stop existing services
echo "Stopping existing services..."
sudo systemctl stop marketingagents 2>/dev/null || true
pm2 stop frontend 2>/dev/null || true

# Start Backend
echo "Starting Backend..."
sudo cp /home/ubuntu/MarketingAgents/deploy/marketingagents.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable marketingagents
sudo systemctl start marketingagents

# Start Frontend with PM2
echo "Starting Frontend..."
cd /home/ubuntu/MarketingAgents/frontend
pm2 start npm --name "frontend" -- run dev
pm2 save

# Setup Nginx
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
    }

    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/marketingagents /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

echo ""
echo "=== Deployed ==="
echo "Check status:"
echo "  pm2 status"
echo "  sudo systemctl status marketingagents"
echo "  sudo systemctl status nginx"
