#!/bin/bash
set -e
REMOTE_HOST="72.56.66.107"
REMOTE_USER="root"
REPO_URL="https://github.com/RockInMyHead/windexsaichat.git"
TARGET_DIR="/opt/windexsaichat"
ENV_VARS="OPENAI_API_KEY=your-api-key-here" # replace securely

# Install dependencies and deploy
ssh @ bash -s <<SSH
set -e
apt-get update -y
apt-get install -y git python3 python3-venv python3-pip
sudo -i -u root bash <<EOT
if [ ! -d  ]; then
  git clone  
fi
cd 
git fetch origin
git reset --hard origin/main
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Write .env if provided (example)
echo  > .env
# Run server in background (adjust as needed; consider using systemd in prod)
nohup uvicorn main:app --host 0.0.0.0 --port 9000 > /var/log/windexai_deploy.log 2>&1 &
EOT
SSH
