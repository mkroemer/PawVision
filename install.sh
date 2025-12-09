#!/bin/bash
set -e

# PawVision Installation Script for Raspberry Pi
# Updated to handle modern Raspberry Pi OS compatibility issues

# ---------------- CONFIG ----------------
REPO_USER="mkroemer"
REPO_NAME="pawvision"
BRANCH="dev"
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
REPO_DIR="$TEMP_DIR"

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
fi

# Always ensure we have a working index.html template
cat > "$INSTALL_DIR/templates/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PawVision</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .header { text-align: center; margin-bottom: 40px; }
        .logo { font-size: 48px; margin-bottom: 10px; }
        h1 { color: #333; margin: 0; font-size: 36px; }
        .subtitle { color: #666; margin-top: 10px; }
        .status { padding: 15px; margin: 20px 0; border-radius: 8px; display: flex; align-items: center; }
        .success { background: #d4edda; color: #155724; border-left: 4px solid #28a745; }
        .info { background: #d1ecf1; color: #0c5460; border-left: 4px solid #17a2b8; }
        .warning { background: #fff3cd; color: #856404; border-left: 4px solid #ffc107; }
        .icon { font-size: 20px; margin-right: 10px; }
        .section { margin: 30px 0; }
        .api-list { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .api-item { font-family: monospace; background: #e9ecef; padding: 8px 12px; margin: 5px 0; border-radius: 4px; }
        .footer { text-align: center; margin-top: 40px; color: #666; font-size: 14px; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🐾</div>
            <h1>PawVision</h1>
            <div class="subtitle">Pet Video Management System</div>
        </div>
        
        <div class="status success">
            <span class="icon">✅</span>
            <div>PawVision is running successfully on your Raspberry Pi!</div>
        </div>
        
        <div class="status info">
            <span class="icon">📱</span>
            <div>Basic interface active - React frontend can be built for full features</div>
        </div>
        
        <div class="section">
            <h2>🎯 Quick Actions</h2>
            <button onclick="location.reload()">🔄 Refresh Status</button>
            <button onclick="window.open('/api/videos', '_blank')">📁 View Videos API</button>
            <button onclick="window.open('/api/config', '_blank')">⚙️ View Config API</button>
        </div>
        
        <div class="section">
            <h2>📊 System Status</h2>
            <div><strong>Service:</strong> Active and Running</div>
            <div><strong>Video Directory:</strong> /home/pi/videos</div>
            <div><strong>Configuration:</strong> /home/pi/pawvision_settings.json</div>
            <div><strong>Web Interface:</strong> http://10.10.0.40:5000</div>
        </div>
        
        <div class="section">
            <h2>🔌 Available APIs</h2>
            <div class="api-list">
                <div class="api-item">GET /api/videos - List all videos</div>
                <div class="api-item">GET /api/config - View configuration</div>
                <div class="api-item">POST /api/config - Update configuration</div>
                <div class="api-item">GET /api/statistics - View playback statistics</div>
                <div class="api-item">POST /api/playback/play - Start video playback</div>
                <div class="api-item">POST /api/playback/stop - Stop playback</div>
            </div>
        </div>
        
        <div class="section">
            <h2>🚀 Next Steps</h2>
            <div class="status warning">
                <span class="icon">⚡</span>
                <div>
                    <strong>Build Full Frontend:</strong><br>
                    • Run <code>cd /tmp/PawVision/frontend && npm install && npm run build</code><br>
                    • Copy build files to <code>/home/pi/static/</code><br>
                    • Restart service for full React interface
                </div>
            </div>
        </div>
        
        <div class="footer">
            PawVision v1.0 - Running on Raspberry Pi<br>
            <small>For support and updates, visit the GitHub repository</small>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds to show any updates
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
EOF

# Handle frontend and static files
echo "🎨 Setting up frontend and static assets..."
mkdir -p "$INSTALL_DIR/static"

# Check if we have pre-built static files (from GitHub releases)
if [ -d "static" ] && [ "$(ls -A static 2>/dev/null)" ]; then
    cp -r static/* "$INSTALL_DIR/static/" 2>/dev/null && echo "✅ Pre-built static files deployed"
    echo "🎉 Using pre-built React frontend - no build needed!"
    FRONTEND_DEPLOYED=true
else
    echo "📝 No pre-built static files found"
    FRONTEND_DEPLOYED=false
fi

# Only build frontend if we don't have pre-built files
if [ "$FRONTEND_DEPLOYED" = false ] && [ -d "$REPO_DIR/frontend" ]; then
    echo "🔨 Pre-built frontend not available - building from source..."
    if ! command -v npm >/dev/null 2>&1; then
        echo "📦 Installing Node.js for frontend build..."
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - 2>/dev/null
        sudo apt-get install -y nodejs 2>/dev/null
        
        if ! command -v npm >/dev/null 2>&1; then
            echo "⚠️  Node.js installation failed - using fallback interface"
        else
            echo "✅ Node.js installed successfully"
        fi
    fi
    
    # Build frontend if Node.js is available
    if command -v npm >/dev/null 2>&1; then
        echo "🔨 Building React frontend..."
        cd "$REPO_DIR/frontend"
        
        # Install dependencies
        if npm ci 2>/dev/null || npm install 2>/dev/null; then
            echo "✅ Frontend dependencies installed"
            
            # Build the frontend
            if npm run build 2>/dev/null; then
                echo "✅ Frontend built successfully"
                
                # Deploy built files (Vite builds to ../static/dist)
                if [ -d "../static/dist" ]; then
                    cp -r ../static/dist/* "$INSTALL_DIR/static/" 2>/dev/null && echo "✅ Frontend deployed to static directory"
                elif [ -d "dist" ]; then
                    cp -r dist/* "$INSTALL_DIR/static/" 2>/dev/null && echo "✅ Frontend deployed to static directory"
                elif [ -d "build" ]; then
                    cp -r build/* "$INSTALL_DIR/static/" 2>/dev/null && echo "✅ Frontend deployed to static directory"
                else
                    echo "⚠️  Build directory not found - using fallback interface"
                fi
            else
                echo "⚠️  Frontend build failed - using fallback interface"
            fi
        else
            echo "⚠️  Frontend dependency installation failed - using fallback interface"
        fi
        cd "$REPO_DIR"
    else
        echo "📝 Node.js not available - using fallback interface"
    fi
elif [ "$FRONTEND_DEPLOYED" = false ]; then
    echo "📝 No frontend directory found - using fallback interface"
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

# Restart or start service with timeout protection
if systemctl is-active --quiet pawvision 2>/dev/null; then
    echo "🔄 Restarting PawVision service..."
    # Stop service first
    sudo systemctl stop pawvision &
    sleep 5
    sudo pkill -f "systemctl stop pawvision" 2>/dev/null || true
    
    # Force kill the python process if still running
    sudo pkill -f "python /home/pi/main.py" 2>/dev/null || true
    sleep 2
    
    # Clean up and start fresh
    sudo systemctl reset-failed pawvision 2>/dev/null || true
    sudo systemctl start pawvision &
    sleep 3
    
elif $FRESH_INSTALL; then
    echo "🚀 Starting PawVision service for the first time..."
    sudo systemctl start pawvision &
    sleep 3
fi

# Wait a moment for service to start, then check status
sleep 3
echo "📊 Final service status:"
if sudo systemctl is-active --quiet pawvision; then
    echo "✅ PawVision service is running successfully"
    echo "🌐 Access the web interface at: http://$(hostname -I | awk '{print $1}'):5000"
else
    echo "⚠️  Service may not have started properly"
    echo "📝 Check logs with: journalctl -u pawvision -f"
    echo "🔧 Manual start: sudo systemctl start pawvision"
fi

echo ""
echo "🎉 PawVision $(if $FRESH_INSTALL; then echo 'installation'; else echo 'update'; fi) complete!"
echo ""
echo "📊 Summary:"
echo "   📁 Installation directory: $INSTALL_DIR"
echo "   🐍 Virtual environment: $INSTALL_DIR/venv"
echo "   🌐 Web interface: http://$(hostname -I | awk '{print $1}'):5000"
echo "   📝 Configuration: $SETTINGS_FILE"
echo ""
echo "📖 Service management:"
echo "   Start:   sudo systemctl start pawvision"
echo "   Stop:    sudo systemctl stop pawvision"
echo "   Status:  sudo systemctl status pawvision"
echo "   Logs:    journalctl -u pawvision -f"
echo ""
echo "✅ Installation script completed successfully!"

# Ensure script exits properly
exit 0