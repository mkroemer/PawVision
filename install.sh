#!/bin/bash
set -e

# PawVision Installation Script for Raspberry Pi
# Updated to handle modern Raspberry Pi OS compatibility issues

# ---------------- CONFIG ----------------
REPO_USER="mkroemer"
REPO_NAME="pawvision"
BRANCH="main"
INSTALL_DIR="/home/pi"
VIDEO_DIR="/media"
SETTINGS_FILE="$INSTALL_DIR/pawvision_settings.json"
SERVICE_FILE="/etc/systemd/system/pawvision.service"
# -----------------------------------------

# Detect fresh install or update
FRESH_INSTALL=false
if [ ! -f "$INSTALL_DIR/main.py" ] || [ ! -f "$SERVICE_FILE" ]; then
    FRESH_INSTALL=true
fi

if $FRESH_INSTALL; then
    echo "🐾 Starting PawVision installation..."
else
    echo "🔄 Updating existing PawVision installation..."
fi

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies - handle usbmount separately as it's not available on newer Pi OS versions
echo "📦 Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv mpv sqlite3 git mediainfo curl

# Try to install usbmount, but don't fail if it's not available
echo "🔌 Attempting to install USB mount support..."
if sudo apt install -y usbmount 2>/dev/null; then
    echo "✅ USB mount support installed"
else
    echo "⚠️  USB mount package not available - USB auto-mounting may not work"
    echo "   You can manually mount USB drives to /media/usb if needed"
fi

# Install VLC for video playback support
echo "📺 Installing VLC components..."
sudo apt install -y vlc-bin vlc-plugin-base libvlc-dev

# Create virtual environment for better dependency isolation
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "$INSTALL_DIR/venv" ]; then
    python3 -m venv "$INSTALL_DIR/venv"
fi
source "$INSTALL_DIR/venv/bin/activate"

# Create necessary directories
mkdir -p "$INSTALL_DIR/videos"
mkdir -p "$INSTALL_DIR/templates"
mkdir -p "$INSTALL_DIR/static"
mkdir -p "$INSTALL_DIR/pawvision"
# Also ensure /media/usb exists for USB-mounted videos
sudo mkdir -p "/media/usb"

# Download and install Python dependencies from requirements.txt
echo "📦 Installing Python dependencies..."
curl -o "$INSTALL_DIR/requirements.txt" \
    -L "https://raw.githubusercontent.com/$REPO_USER/$REPO_NAME/$BRANCH/requirements.txt"
source "$INSTALL_DIR/venv/bin/activate"
echo "📦 Installing Python dependencies (this may take a while)..."
if pip install -r "$INSTALL_DIR/requirements.txt"; then
    echo "✅ Python dependencies installed successfully"
else
    echo "❌ Error installing Python dependencies. Trying with --break-system-packages..."
    pip install -r "$INSTALL_DIR/requirements.txt" --break-system-packages
fi

# Clone the entire repository to get all files
echo "📥 Downloading latest PawVision files..."
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"
git clone --depth 1 -b "$BRANCH" "https://github.com/$REPO_USER/$REPO_NAME.git" .

# Copy all Python files
echo "🐍 Copying main Python files..."
cp main.py "$INSTALL_DIR/" 2>/dev/null || echo "No main.py found"
cp pawvision.py "$INSTALL_DIR/" 2>/dev/null || echo "No pawvision.py found (redirect script)"

# Copy pawvision module
echo "📦 Copying pawvision module..."
cp -r pawvision/ "$INSTALL_DIR/" 2>/dev/null || echo "No pawvision module found"

# Copy templates directory
echo "📄 Copying templates..."
if [ -d "templates" ]; then
    cp -r templates/* "$INSTALL_DIR/templates/" 2>/dev/null || echo "Template directory exists but is empty"
else
    echo "No templates directory found - creating fallback template"
    mkdir -p "$INSTALL_DIR/templates"
    cat > "$INSTALL_DIR/templates/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PawVision</title>
    <link rel="icon" type="image/png" href="/static/dist/pawvision.png">
</head>
<body>
    <div id="root"></div>
    <script type="module" src="/static/dist/assets/index.js"></script>
</body>
</html>
EOF
fi

# Copy static directory (includes built frontend)
echo "🎨 Copying static assets and frontend..."
if [ -d "static" ]; then
    cp -r static/* "$INSTALL_DIR/static/" 2>/dev/null || echo "Static directory exists but is empty"
else
    echo "⚠️  No static directory found - frontend may not work properly"
    mkdir -p "$INSTALL_DIR/static"
fi

# Copy any other important files
cp requirements.txt "$INSTALL_DIR/" 2>/dev/null || echo "No requirements.txt found"
cp .gitignore "$INSTALL_DIR/" 2>/dev/null || echo "No .gitignore found"

# Clean up
cd - > /dev/null
rm -rf "$TEMP_DIR"

# Ensure proper ownership
sudo chown -R pi:pi "$INSTALL_DIR"
sudo chown -R pi:pi "/media/usb" 2>/dev/null || echo "Note: /media/usb ownership will be set when USB is mounted"

# Make sure venv is properly owned and scripts are executable
sudo chown -R pi:pi "$INSTALL_DIR/venv" 2>/dev/null || echo "Virtual environment ownership already correct"
chmod +x "$INSTALL_DIR/main.py" 2>/dev/null || echo "main.py already executable"

# Handle settings - the new system automatically creates defaults if no config exists
if [ ! -f "$SETTINGS_FILE" ]; then
    echo "📝 Settings file will be created automatically on first run with default values"
else
    echo "🔄 Existing settings file preserved: $SETTINGS_FILE"
    echo "   New settings will be merged automatically if needed"
fi

# Create systemd service if fresh install
if $FRESH_INSTALL; then
    echo "⚙️ Creating systemd service..."
    sudo bash -c "cat > $SERVICE_FILE" <<EOL
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
EOL
    sudo systemctl daemon-reload
    sudo systemctl enable pawvision
fi

# Test the installation
echo "🧪 Testing PawVision installation..."
source "$INSTALL_DIR/venv/bin/activate"
cd "$INSTALL_DIR"

# Test Python module import
if python3 -c "import pawvision; print('✅ PawVision module loads successfully')" 2>/dev/null; then
    echo "✅ Module test passed"
else
    echo "⚠️  Warning: PawVision module test failed - checking dependencies..."
    python3 -c "
import sys
try:
    import flask
    print('✅ Flask available')
except ImportError:
    print('❌ Flask not available')
try:
    import vlc
    print('✅ VLC bindings available') 
except ImportError:
    print('❌ VLC Python bindings not available')
"
fi

# Only restart service if it exists and we're updating
if systemctl is-active --quiet pawvision 2>/dev/null; then
    echo "🔄 Restarting PawVision service..."
    sudo systemctl restart pawvision
elif $FRESH_INSTALL; then
    echo "🚀 Starting PawVision service for the first time..."
    sudo systemctl start pawvision
fi

# Check service status
echo "📊 Service status:"
sudo systemctl status pawvision --no-pager --lines=3 || echo "Service not running - check logs with: journalctl -u pawvision -f"

if $FRESH_INSTALL; then
    echo "✅ PawVision installation complete!"
    echo "🌐 Access the web UI at: http://<pi-ip>:5000"
    echo "📁 Installation directory: $INSTALL_DIR"
    echo "🐍 Virtual environment: $INSTALL_DIR/venv"
    echo "⚙️  Service status: systemctl status pawvision"
else
    echo "✅ PawVision update complete!"
    echo "🚀 Service restarted with latest version."
    echo "📝 Check logs: journalctl -u pawvision -f"
fi

echo ""
echo "📖 Quick commands:"
echo "   Start:   sudo systemctl start pawvision"
echo "   Stop:    sudo systemctl stop pawvision"
echo "   Status:  sudo systemctl status pawvision"
echo "   Logs:    journalctl -u pawvision -f"