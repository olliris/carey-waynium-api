#!/bin/bash

echo "🚀 Starting Carey → Waynium API setup..."

# Create working directory
mkdir -p /opt/carey-waynium-api
cd /opt/carey-waynium-api || exit

# Update & install dependencies
apt update && apt install -y python3-pip python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install flask python-dotenv requests pyjwt

#upload content from github with curl
cd /opt/carey-waynium-api
curl -o main.py https://raw.githubusercontent.com/olliris/carey-waynium-api/main/main.py

# Instructions to finish manually
echo "✅ Setup complete."
echo "➡️ Next steps:"
echo "1. Create your .env file in /opt/carey-waynium-api"
echo "2. Create main.py and implement your Flask server"
echo "3. Run it with: source venv/bin/activate && python main.py"
