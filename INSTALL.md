# Installation Options

PawVision now offers two installation methods:

## 🚀 Quick Install (Recommended)
Uses pre-built packages from GitHub releases - **no building required!**

```bash
# Download the GitHub release installer
wget https://raw.githubusercontent.com/mkroemer/PawVision/dev/github-install.sh

# Make executable and run
chmod +x github-install.sh
sudo ./github-install.sh
```

**Benefits:**
- ✅ Fastest installation (no building)
- ✅ No Node.js required
- ✅ Pre-built React frontend
- ✅ Automatic updates from releases

## 🔨 Source Install
Uses the traditional install script - builds from source

```bash
# Download the source installer  
wget https://raw.githubusercontent.com/mkroemer/PawVision/dev/install.sh

# Make executable and run
chmod +x install.sh
sudo ./install.sh
```

**Benefits:**
- ✅ Always uses latest code
- ✅ Automatically detects pre-built files
- ✅ Falls back to building if needed
- ✅ Development-friendly

## 📦 Manual Package Install
If you already have a downloaded package:

```bash
# Extract the package
tar -xzf pawvision-package.tar.gz
cd pawvision

# Run the package installer
chmod +x package-install.sh
./package-install.sh
```

---

**Recommendation:** Use the **Quick Install** method for production deployments on Raspberry Pi systems. It's faster and doesn't require Node.js installation.