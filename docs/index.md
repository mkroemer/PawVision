---
layout: home
title: 🐾 PawVision Documentation
---
<div style="text-align: center; margin-bottom: 2rem;">
  <img src="pawvision.png" alt="PawVision Logo" height="200"/>
</div>

PawVision is a Raspberry Pi-based "Pet TV" system that plays random videos for your pet on an HDMI monitor with a pet-friendly web interface.

## Key Features

- **Smart Video Playback**: Local video library with random selection and timing
- **Night Mode**: Automatic volume control during sleeping hours
- **Physical Controls**: GPIO button with configurable behavior
- **Motion Detection**: Optional motion sensor integration
- **Web Interface**: Modern, pet-friendly control panel
- **Scheduling**: Automated playback at set times
- **Statistics**: Track viewing patterns and usage

## Quick Start

1. **Install on Raspberry Pi**:

   ```bash
   curl -sSL https://raw.githubusercontent.com/mkroemer/pawvision/main/install.sh | bash
   ```
2. **Access Web Interface**:
   Open `http://<pi-ip>:5000` in your browser
3. **Upload Videos**:
   Use the web interface to upload your pet's favorite videos
4. **Configure Settings**:
   Customize timing, volume, and hardware settings

## Documentation

- [📋 Configuration Guide](configuration.html) - Complete setup and configuration
- [🔌 API Reference](api.html) - REST API documentation
- [📝 Release Notes](releases.html) - Latest updates and changes
- [🛠️ Hardware Setup](hardware.md) - How to connect and configure hardware

## Support

For issues, feature requests, or contributions, visit our [GitHub repository](https://github.com/mkroemer/PawVision).
