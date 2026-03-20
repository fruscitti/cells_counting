#!/usr/bin/env bash
# deploy.sh — Idempotent deployment script for celulas cell counter app
# Usage: bash deploy.sh
# Safe to re-run at any time for updates.

set -e

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REMOTE=ferar@ferar.cloud
REMOTE_DIR=/home/ferar/projects/celulas
APP_PORT=7860
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "===> Deploying celulas to $REMOTE:$REMOTE_DIR"

# ---------------------------------------------------------------------------
# Section 1: Install system dependencies
# ---------------------------------------------------------------------------
echo ""
echo "===> [1/7] Installing system dependencies..."
ssh "$REMOTE" bash -s << 'ENDSSH'
set -e
sudo apt-get update -qq
sudo apt-get install -y nginx certbot python3-certbot-nginx libgl1 libglib2.0-0

# Install uv if not present
if [ ! -f "$HOME/.local/bin/uv" ]; then
    echo "---> Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
else
    echo "---> uv already installed, skipping"
fi
mkdir -p "$HOME/projects/celulas"
ENDSSH

# ---------------------------------------------------------------------------
# Section 2: Rsync app files to VPS
# ---------------------------------------------------------------------------
echo ""
echo "===> [2/7] Syncing app files to VPS..."
rsync -avz --delete \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='images/' \
    --exclude='verified_counts/' \
    --exclude='output/' \
    --exclude='.planning/' \
    --exclude='.git/' \
    "$SCRIPT_DIR/" "$REMOTE:$REMOTE_DIR/"

# Copy OG image to nginx web root so it's publicly accessible at /og-image.png
ssh "$REMOTE" "sudo cp $REMOTE_DIR/static/og-image.png /var/www/html/og-image.png"

# ---------------------------------------------------------------------------
# Section 3: Create venv and install Python dependencies
# ---------------------------------------------------------------------------
echo ""
echo "===> [3/7] Setting up Python environment and installing dependencies..."
ssh "$REMOTE" bash -s << ENDSSH
set -e
cd "$REMOTE_DIR"

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "---> Creating venv..."
    ~/.local/bin/uv venv .venv
else
    echo "---> venv already exists, skipping creation"
fi

# Install/update dependencies
echo "---> Installing Python dependencies..."
~/.local/bin/uv pip install --python .venv/bin/python \
    opencv-python-headless pandas numpy gradio uvicorn
ENDSSH

# ---------------------------------------------------------------------------
# Section 4: Create systemd service
# ---------------------------------------------------------------------------
echo ""
echo "===> [4/7] Installing systemd service..."
ssh "$REMOTE" bash -s << ENDSSH
set -e
sudo tee /etc/systemd/system/celulas.service > /dev/null << 'SERVICE'
[Unit]
Description=Celulas Cell Counter
After=network.target

[Service]
User=ferar
WorkingDirectory=/home/ferar/projects/celulas
ExecStart=/home/ferar/.local/bin/uv run --python .venv/bin/python main.py
Restart=always
RestartSec=3
Environment=GRADIO_SERVER_NAME=127.0.0.1
Environment=GRADIO_SERVER_PORT=7860

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable celulas
echo "---> systemd service installed and enabled"
ENDSSH

# ---------------------------------------------------------------------------
# Section 5: Create nginx config
# ---------------------------------------------------------------------------
echo ""
echo "===> [5/7] Configuring nginx..."
ssh "$REMOTE" bash -s << 'ENDSSH'
set -e
sudo tee /etc/nginx/sites-available/celulas > /dev/null << 'NGINX'
server {
    listen 80;
    server_name ferar.cloud;

    location = /og-image.png {
        root /var/www/html;
    }

    location /cc/ {
        proxy_pass http://127.0.0.1:7860/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
        client_max_body_size 50M;
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/celulas /etc/nginx/sites-enabled/celulas
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
echo "---> nginx configured and reloaded"
ENDSSH

# ---------------------------------------------------------------------------
# Section 6: SSL via certbot (skipped if cert already exists)
# ---------------------------------------------------------------------------
echo ""
echo "===> [6/7] Checking SSL certificate..."
ssh "$REMOTE" bash -s << 'ENDSSH'
set -e
if sudo test -d /etc/letsencrypt/live/ferar.cloud; then
    echo "---> SSL cert already exists, skipping certbot"
else
    echo "---> Requesting SSL certificate via certbot..."
    sudo certbot --nginx -d ferar.cloud \
        --non-interactive --agree-tos \
        --email ferar@ferar.cloud
fi
ENDSSH

# ---------------------------------------------------------------------------
# Section 7: Start/restart app and verify
# ---------------------------------------------------------------------------
echo ""
echo "===> [7/7] Starting celulas service..."
ssh "$REMOTE" bash -s << 'ENDSSH'
set -e
sudo systemctl restart celulas
sleep 3
STATUS=$(sudo systemctl is-active celulas)
if [ "$STATUS" = "active" ]; then
    echo "---> celulas is running (status: active)"
else
    echo "ERROR: celulas failed to start (status: $STATUS)"
    sudo systemctl status celulas --no-pager
    exit 1
fi
ENDSSH

echo ""
echo "===> Deployed! Visit https://ferar.cloud/cc"
