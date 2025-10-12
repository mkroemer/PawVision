#!/bin/bash

# PawVision Frontend Setup Script

echo "🐾 Setting up PawVision React Frontend..."

# Navigate to frontend directory
cd "$(dirname "$0")"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js v18 or higher."
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm."
    exit 1
fi

echo "✅ npm $(npm -v) detected"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Copy logo if it doesn't exist
if [ ! -f "public/pawvision.png" ]; then
    if [ -f "../static/pawvision.png" ]; then
        echo "📋 Copying logo..."
        mkdir -p public
        cp ../static/pawvision.png public/
        echo "✅ Logo copied"
    else
        echo "⚠️  Warning: Logo file not found at ../static/pawvision.png"
    fi
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "Available commands:"
echo "  npm run dev      - Start development server (http://localhost:3000)"
echo "  npm run build    - Build for production"
echo "  npm run preview  - Preview production build"
echo "  npm run lint     - Run ESLint"
echo ""
echo "To get started:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
