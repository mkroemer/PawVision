#!/bin/bash
# PawVision GitHub Release Installer
# Downloads and installs the latest PawVision release from GitHub

set -e  # Exit on any error

# Configuration
REPO_USER="mkroemer"
REPO_NAME="PawVision"
INSTALL_DIR="/home/pi/pawvision"
SERVICE_NAME="pawvision"
SYSTEM_USER="pi"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐾 PawVision Release Installer${NC}"
echo "================================"

# Check if running as root (for system package installation)
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}⚠️  This script needs sudo privileges for system packages${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

# Function to get latest release URL
get_latest_release() {
    echo -e "${BLUE}📦 Finding latest PawVision release...${NC}"
    local api_response=$(curl -s "https://api.github.com/repos/$REPO_USER/$REPO_NAME/releases/latest")
    local download_url=$(echo "$api_response" | grep -o '"browser_download_url": "[^"]*pawvision-package.tar.gz"' | cut -d'"' -f4)
    
    if [ -z "$download_url" ]; then
        echo -e "${RED}❌ Could not find latest release package${NC}"
        echo "Available releases: https://github.com/$REPO_USER/$REPO_NAME/releases"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Found latest release${NC}"
    echo "$download_url"
}

# Function to install system dependencies
install_system_deps() {
    echo -e "${BLUE}📦 Installing system dependencies...${NC}"
    
    # Update package list
    apt-get update -qq
    
    # Install required packages
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        vlc \
        vlc-plugin-base \
        python3-vlc \
        mpv \
        mediainfo \
        curl \
        wget \
        tar \
        systemd > /dev/null 2>&1
    
    echo -e "${GREEN}✅ System dependencies installed${NC}"
}

# Function to download and install package
install_package() {
    local download_url="$1"
    
    echo -e "${BLUE}⬇️  Downloading and installing PawVision...${NC}"
    
    # Create temporary directory
    local temp_dir=$(mktemp -d)
    cd "$temp_dir"
    
    # Download package
    if ! wget -q --show-progress "$download_url" -O pawvision-package.tar.gz; then
        echo -e "${RED}❌ Failed to download package${NC}"
        rm -rf "$temp_dir"
        exit 1
    fi
    
    # Extract package
    if ! tar -xzf pawvision-package.tar.gz; then
        echo -e "${RED}❌ Failed to extract package${NC}"
        rm -rf "$temp_dir"
        exit 1
    fi
    
    # Stop existing service if running
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    
    # Backup old settings if they exist
    local settings_backup=""
    if [ -f "$INSTALL_DIR/pawvision_settings.json" ]; then
        settings_backup=$(mktemp)
        cp "$INSTALL_DIR/pawvision_settings.json" "$settings_backup"
        echo -e "${BLUE}💾 Backed up existing settings${NC}"
    fi
    
    # Remove old installation
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "${YELLOW}🗑️  Removing old installation...${NC}"
        rm -rf "$INSTALL_DIR"
    fi
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    # Move extracted files to install directory
    if [ -d "pawvision" ]; then
        cp -r pawvision/* "$INSTALL_DIR/"
        echo -e "${GREEN}✅ Package installed to $INSTALL_DIR${NC}"
    else
        echo -e "${RED}❌ Package structure is invalid${NC}"
        rm -rf "$temp_dir"
        exit 1
    fi
    
    # Restore settings if they existed
    if [ -n "$settings_backup" ] && [ -f "$settings_backup" ]; then
        cp "$settings_backup" "$INSTALL_DIR/pawvision_settings.json"
        rm "$settings_backup"
        echo -e "${GREEN}✅ Restored previous settings${NC}"
    fi
    
    # Clean up
    cd - > /dev/null
    rm -rf "$temp_dir"
}

# Function to setup Python environment
setup_python_env() {
    echo -e "${BLUE}🐍 Setting up Python environment...${NC}"
    
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    python3 -m venv venv
    
    # Install Python dependencies
    ./venv/bin/pip install --upgrade pip > /dev/null
    ./venv/bin/pip install -r requirements.txt > /dev/null
    
    echo -e "${GREEN}✅ Python environment configured${NC}"
}

# Function to create systemd service
create_service() {
    echo -e "${BLUE}⚙️  Creating systemd service...${NC}"
    
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=PawVision - Pet Video Management System
After=network.target multi-user.target
Wants=network.target

[Service]
Type=simple
User=$SYSTEM_USER
Group=$SYSTEM_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Security settings
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$INSTALL_DIR /media/usb /tmp
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
EOF

    # Set proper ownership
    chown -R "$SYSTEM_USER:$SYSTEM_USER" "$INSTALL_DIR"
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    
    echo -e "${GREEN}✅ Service created and enabled${NC}"
}

# Function to start service
start_service() {
    echo -e "${BLUE}🚀 Starting PawVision service...${NC}"
    
    if systemctl start "$SERVICE_NAME"; then
        sleep 3
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            echo -e "${GREEN}✅ PawVision is running!${NC}"
            
            # Get the local IP
            local ip_addr=$(hostname -I | awk '{print $1}')
            
            echo ""
            echo -e "${GREEN}🌐 Web interface available at:${NC}"
            echo -e "   http://$ip_addr:5000"
            echo -e "   http://localhost:5000"
            echo ""
            echo -e "${BLUE}📋 Useful commands:${NC}"
            echo -e "   Status:  ${YELLOW}sudo systemctl status $SERVICE_NAME${NC}"
            echo -e "   Stop:    ${YELLOW}sudo systemctl stop $SERVICE_NAME${NC}"
            echo -e "   Restart: ${YELLOW}sudo systemctl restart $SERVICE_NAME${NC}"
            echo -e "   Logs:    ${YELLOW}sudo journalctl -u $SERVICE_NAME -f${NC}"
        else
            echo -e "${RED}❌ Service failed to start${NC}"
            echo "Check logs: sudo journalctl -u $SERVICE_NAME -n 20"
            exit 1
        fi
    else
        echo -e "${RED}❌ Failed to start service${NC}"
        exit 1
    fi
}

# Main installation process
main() {
    echo -e "${BLUE}Starting PawVision installation...${NC}"
    echo ""
    
    # Get latest release URL
    local download_url=$(get_latest_release)
    
    # Install system dependencies
    install_system_deps
    
    # Download and install the package
    install_package "$download_url"
    
    # Setup Python environment
    setup_python_env
    
    # Create systemd service
    create_service
    
    # Start the service
    start_service
    
    echo ""
    echo -e "${GREEN}🎉 PawVision installation completed!${NC}"
    echo -e "${BLUE}The pre-built React frontend is ready to use.${NC}"
}

# Run main installation
main "$@"