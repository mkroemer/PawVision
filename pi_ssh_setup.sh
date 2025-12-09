#!/bin/bash

# PawVision Pi SSH Setup Guide
echo "🔐 PawVision Pi SSH Setup Guide"
echo "==============================="
echo ""

echo "Since SSH is not currently enabled on your Pi at 10.10.0.40,"
echo "you'll need to enable it first. Here are several methods:"
echo ""

echo "📋 Method 1: Using raspi-config (if you have keyboard/monitor access)"
echo "1. Connect keyboard and monitor to your Pi"
echo "2. Open terminal and run:"
echo "   sudo raspi-config"
echo "3. Navigate to: 'Interface Options' > 'SSH' > 'Enable'"
echo "4. Reboot the Pi"
echo ""

echo "📋 Method 2: Using command line (if you have terminal access)"
echo "1. Connect to Pi via keyboard/monitor"
echo "2. Run these commands:"
echo "   sudo systemctl enable ssh"
echo "   sudo systemctl start ssh"
echo ""

echo "📋 Method 3: Enable SSH on boot (if you can access SD card)"
echo "1. Remove SD card from Pi and insert into computer"
echo "2. In the boot partition, create an empty file named 'ssh'"
echo "   touch /Volumes/bootfs/ssh  # On macOS"
echo "3. Insert SD card back into Pi and power on"
echo ""

echo "📋 Method 4: Enable via GPIO (advanced users)"
echo "If you have GPIO access, you can use a serial connection"
echo ""

echo "🔧 After enabling SSH:"
echo "1. Run the deployment script:"
echo "   ./deploy_to_pi.sh"
echo "2. The script will automatically install PawVision"
echo ""

echo "🌐 Default SSH credentials for Raspberry Pi OS:"
echo "   Username: pi"
echo "   Password: raspberry (change this after first login!)"
echo ""

echo "📞 Need help? Check the Pi's actual IP address:"
echo "   - On Pi: hostname -I"
echo "   - From router admin panel"
echo "   - Network scanner: nmap -sn 10.10.0.0/24"