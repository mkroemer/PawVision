#!/bin/bash
set -e

# PawVision Package Installer
# This script installs a pre-built PawVision package

echo "🐾 PawVision Package Installer"
echo "================================"

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -d "pawvision" ]; then
    echo "❌ Error: This doesn't look like a PawVision package directory"
    echo "Make sure you've extracted the package and are running from the pawvision/ directory"
    exit 1
fi

# Configuration
INSTALL_DIR="/home/pi"
SERVICE_FILE="/etc/systemd/system/pawvision.service"
SETTINGS_FILE="$INSTALL_DIR/pawvision_settings.json"

# Detect fresh install or update
FRESH_INSTALL=false
if [ ! -f "$INSTALL_DIR/main.py" ] || [ ! -f "$SERVICE_FILE" ]; then
    FRESH_INSTALL=true
fi

if $FRESH_INSTALL; then
    echo "🆕 Fresh installation detected"
else
    echo "🔄 Updating existing installation"
fi

# Update system and install dependencies
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv mpv sqlite3 mediainfo curl

# Install VLC components
echo "📺 Installing VLC components..."
sudo apt install -y vlc-bin vlc-plugin-base libvlc-dev || echo "⚠️ Some VLC components may not be available"

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "$INSTALL_DIR/venv" ]; then
    python3 -m venv "$INSTALL_DIR/venv"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
source "$INSTALL_DIR/venv/bin/activate"
pip install -r requirements.txt

# Copy all files
echo "📁 Installing PawVision files..."
cp main.py "$INSTALL_DIR/"
cp -r pawvision/ "$INSTALL_DIR/"
cp -r templates/ "$INSTALL_DIR/"
cp -r static/ "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"

# Set permissions
sudo chown -R pi:pi "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/main.py"

# Create directories
mkdir -p "$INSTALL_DIR/videos"
sudo mkdir -p "/media/usb"

# Preserve existing settings
if [ -f "$SETTINGS_FILE" ]; then
    echo "🔄 Preserving existing settings"
else
    echo "📝 Settings will be created on first run"
fi

# Create or update systemd service
echo "⚙️ Setting up systemd service..."
sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=PawVision Service
After=network.target

[Service]
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py
Restart=always
User=pi
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable pawvision

# Test installation
echo "🧪 Testing installation..."
source "$INSTALL_DIR/venv/bin/activate"
cd "$INSTALL_DIR"
if python3 -c "import pawvision; print('✅ PawVision module loads successfully')" 2>/dev/null; then
    echo "✅ Installation test passed"
else
    echo "⚠️ Warning: Installation test failed"
fi

# Start/restart service
if systemctl is-active --quiet pawvision 2>/dev/null; then
    echo "🔄 Restarting PawVision service..."
    sudo systemctl restart pawvision
else
    echo "🚀 Starting PawVision service..."
    sudo systemctl start pawvision
fi

# Wait and check status
sleep 3
if sudo systemctl is-active --quiet pawvision; then
    echo "✅ PawVision service started successfully"
    PI_IP=$(hostname -I | awk '{print $1}')
    echo "🌐 Web interface: http://$PI_IP:5000"
else
    echo "⚠️ Service may not have started properly"
    echo "Check logs: journalctl -u pawvision -f"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📊 Summary:"
echo "   📁 Installation: $INSTALL_DIR"
echo "   🌐 Web interface: http://$(hostname -I | awk '{print $1}'):5000"
echo "   📝 Logs: journalctl -u pawvision -f"
echo "   ⚙️ Status: systemctl status pawvision"
echo ""

# Show build info if available
if [ -f "BUILD_INFO" ]; then
    echo "📋 Package Info:"
    cat BUILD_INFO | sed 's/^/   /'
    echo ""
fi

echo "✅ Ready to use!"