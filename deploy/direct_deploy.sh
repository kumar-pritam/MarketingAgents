#!/bin/bash

set -e

echo "=== Direct Deployment (No Docker) ==="

# Install Node.js
echo "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python & pip
echo "Installing Python..."
sudo apt install -y python3 python3-pip python3-venv

# Install nginx
echo "Installing nginx..."
sudo apt install -y nginx

# Setup Backend
echo "Setting up Backend..."
cd ~/MarketingAgents/backend
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup Frontend
echo "Setting up Frontend..."
cd ~/MarketingAgents/frontend
npm install --legacy-peer-deps

# Configure nginx
echo "Configuring nginx..."
sudo tee /etc/nginx/sites-available/marketingagents > /dev/null <<'EOF'
upstream frontend {
    server 127.0.0.1:3000;
}

upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_http_version 1.1;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/marketingagents /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# Start Backend
echo "Starting Backend..."
cd ~/MarketingAgents/backend
source .venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &

# Start Frontend
echo "Starting Frontend..."
cd ~/MarketingAgents/frontend
nohup npm start > /tmp/frontend.log 2>&1 &

echo ""
echo "=== Done! ==="
echo "Access at: http://13.232.143.135"
echo ""
echo "Backend: http://13.232.143.135:8000"
echo "Frontend: http://13.232.143.135:3000"