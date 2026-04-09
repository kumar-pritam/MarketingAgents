#!/bin/bash

set -e

echo "=== MarketingAgents EC2 Setup ==="

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.12-venv python3-pip nginx certbot python3-certbot-nginx

# Create app directory
sudo mkdir -p /home/ubuntu/MarketingAgents
sudo chown ubuntu:ubuntu /home/ubuntu/MarketingAgents

# Clone repo (run manually with your token)
# git clone https://github.com/kumar-pritam/MarketingAgents.git /home/ubuntu/MarketingAgents

# Create virtual environment
cd /home/ubuntu/MarketingAgents
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup systemd service
sudo cp marketingagents.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable marketingagents
sudo systemctl start marketingagents

# Setup Nginx
sudo cp nginx.conf /etc/nginx/sites-available/marketingagents
sudo ln -sf /etc/nginx/sites-available/marketingagents /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default 2>/dev/null || true
sudo nginx -t
sudo systemctl reload nginx

# Setup SSL (after DNS points to this server)
# sudo certbot --nginx -d yourdomain.com

echo "=== Setup Complete ==="
echo "App running at: http://YOUR_EC2_IP"
echo "Status: sudo systemctl status marketingagents"
