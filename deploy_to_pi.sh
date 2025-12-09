#!/bin/bash
set -e

# PawVision Pi Deployment Script
PI_IP="10.10.0.40"
PI_USER="pi"
LOCAL_PROJECT_DIR="/Users/markus/Documents/Coding/PawVision"

echo "🚀 Deploying PawVision to Raspberry Pi at $PI_IP"

# Check if we can connect to the Pi
echo "🔍 Checking Pi connectivity..."
if ! ping -c 1 "$PI_IP" >/dev/null 2>&1; then
    echo "❌ Error: Cannot reach Pi at $PI_IP"
    echo "Please check:"
    echo "  - Pi is powered on"
    echo "  - Network connection is working"
    echo "  - IP address is correct"
    exit 1
fi

echo "✅ Pi is reachable"

# Test SSH connection
echo "🔐 Testing SSH connection..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$PI_USER@$PI_IP" exit 2>/dev/null; then
    echo "❌ Cannot connect via SSH to $PI_USER@$PI_IP"
    echo ""
    echo "To enable SSH on your Raspberry Pi:"
    echo "1. Connect keyboard/monitor to Pi"
    echo "2. Run: sudo raspi-config"
    echo "3. Go to 'Interfacing Options' -> 'SSH' -> 'Enable'"
    echo "4. Or enable via command line: sudo systemctl enable ssh && sudo systemctl start ssh"
    echo ""
    echo "Alternative: Create empty 'ssh' file in /boot partition to enable SSH on boot"
    exit 1
fi

echo "✅ SSH connection successful"

# Create deployment directory on Pi
echo "📁 Creating deployment directory..."
ssh "$PI_USER@$PI_IP" "mkdir -p /tmp/pawvision_deploy"

# Copy project files to Pi
echo "📤 Copying project files..."
rsync -avz --progress --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='node_modules' --exclude='venv' --exclude='videos' \
    "$LOCAL_PROJECT_DIR/" "$PI_USER@$PI_IP:/tmp/pawvision_deploy/"

# Copy and run the installation script
echo "🔧 Running installation script on Pi..."
ssh "$PI_USER@$PI_IP" "cd /tmp/pawvision_deploy && chmod +x install.sh && ./install.sh"

# Check service status
echo "📊 Checking service status..."
ssh "$PI_USER@$PI_IP" "systemctl status pawvision --no-pager"

# Get Pi IP for web interface
PI_LOCAL_IP=$(ssh "$PI_USER@$PI_IP" "hostname -I | awk '{print \$1}'")

echo ""
echo "✅ Deployment complete!"
echo "🌐 Web interface: http://$PI_LOCAL_IP:5000"
echo "📊 Service status: ssh $PI_USER@$PI_IP 'systemctl status pawvision'"
echo "📝 View logs: ssh $PI_USER@$PI_IP 'journalctl -u pawvision -f'"
echo ""
echo "🔧 Useful commands:"
echo "  Restart service: ssh $PI_USER@$PI_IP 'sudo systemctl restart pawvision'"
echo "  Stop service: ssh $PI_USER@$PI_IP 'sudo systemctl stop pawvision'"
echo "  Update code: $0"