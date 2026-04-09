#!/bin/bash

set -e

echo "=== Updating MarketingAgents ==="

cd /home/ubuntu/MarketingAgents

# Pull latest code
git pull origin main

# Activate venv and reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart marketingagents

echo "=== Update Complete ==="
echo "Status: sudo systemctl status marketingagents"
