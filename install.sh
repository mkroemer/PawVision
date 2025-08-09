#!/bin/bash
set -e

# ---------------- CONFIG ----------------
REPO_USER="mkroemer"
REPO_NAME="pawvision"
BRANCH="main"
INSTALL_DIR="/home/pi"
SETTINGS_FILE="$INSTALL_DIR/pawvision_settings.json"
DEFAULT_SETTINGS_URL="https://raw.githubusercontent.com/$REPO_USER/$REPO_NAME/$BRANCH/default_settings.json"
SERVICE_FILE="/etc/systemd/system/pawvision.service"
# -----------------------------------------

# Detect fresh install or update
FRESH_INSTALL=false
if [ ! -f "$INSTALL_DIR/pawvision.py" ] || [ ! -f "$SERVICE_FILE" ]; then
    FRESH_INSTALL=true
fi

if $FRESH_INSTALL; then
    echo "🐾 Starting PawVision installation..."
else
    echo "🔄 Updating existing PawVision installation..."
fi

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip mpv sqlite3 git mediainfo usbmount curl jq
pip3 install flask gpiozero

# Create directories
mkdir -p "$INSTALL_DIR/videos"
mkdir -p "$INSTALL_DIR/templates"
sudo chown -R pi:pi "$INSTALL_DIR/videos" "$INSTALL_DIR/templates"

# Download latest Python script
echo "📥 Downloading latest PawVision script..."
curl -o "$INSTALL_DIR/pawvision.py" \
    -L "https://raw.githubusercontent.com/$REPO_USER/$REPO_NAME/$BRANCH/pawvision.py"

# Download latest HTML template
curl -o "$INSTALL_DIR/templates/index.html" \
    -L "https://raw.githubusercontent.com/$REPO_USER/$REPO_NAME/$BRANCH/templates/index.html"

# Handle settings
if [ ! -f "$SETTINGS_FILE" ]; then
    echo "📝 Creating default settings..."
    curl -o "$SETTINGS_FILE" -L "$DEFAULT_SETTINGS_URL"
    sudo chown pi:pi "$SETTINGS_FILE"
else
    echo "🔄 Merging new settings keys (if any)..."
    TMP_FILE=$(mktemp)
    curl -o "$TMP_FILE" -L "$DEFAULT_SETTINGS_URL"
    # Merge new keys without overwriting existing ones
    jq -s '.[0] * .[1]' "$TMP_FILE" "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp"
    mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
    rm "$TMP_FILE"
    sudo chown pi:pi "$SETTINGS_FILE"
fi

# Create systemd service if fresh install
if $FRESH_INSTALL; then
    echo "⚙️ Creating systemd service..."
    sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=PawVision Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 $INSTALL_DIR/pawvision.py
Restart=always
User=pi
WorkingDirectory=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOL
    sudo systemctl daemon-reload
    sudo systemctl enable pawvision
fi

# Restart service to apply updates
sudo systemctl restart pawvision

if $FRESH_INSTALL; then
    echo "✅ PawVision installation complete!"
    echo "🌐 Access the web UI at: http://<pi-ip>:5000"
else
    echo "✅ PawVision update complete!"
    echo "🚀 Service restarted with latest version."
fi