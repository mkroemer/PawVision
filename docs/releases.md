layout: page
title: Release Notes
permalink: /releases/

## Version 1.0.0 - August 2025
### 📋 Configuration Schema
### 🎯 Major Features
**New Settings:**
**Centralized Time Utilities**
- Unified time parsing system
- Eliminated duplicate code across modules
- Improved consistency and maintainability
```json
**Motion Detection Enhancements**
- Motion-based video stopping
- Configurable timeout for no-motion detection
- Enhanced pet engagement tracking
{
**Settings UI Redesign**
- Themed cards for settings
- Improved visual hierarchy and usability
- Better mobile responsiveness
  "post_playback_cooldown_minutes": 5,
**Enhanced Statistics System**
- SQLite database for persistent storage
- Detailed viewing analytics and patterns
- Chart.js integration for visual insights
- Per-video performance tracking
  "button_cooldown_seconds": 60,
**Advanced Motion Detection**
- GPIO motion sensor integration
- Configurable sensitivity and timing
- Automatic video stopping when pet walks away
- Motion event logging and analytics
  "motion_sensor_enabled": false,
**Improved Time Precision**
- HH:MM format support for all time settings
- Minute-level precision for scheduling
- Enhanced validation and error handling
  "motion_sensor_pin": null,
**Modern Web Interface**
- Redesigned with pet-friendly color scheme
- Interactive statistics dashboard
- Real-time status updates
  "enable_statistics": true,
**Button Control Enhancements**
- Configurable cooldown periods
- Time-based disable scheduling
- Second-press stop functionality
- Better debouncing and reliability
  "statistics_db": "./pawvision_stats.db"
**Video Management**
- Improved file upload handling
- Better format validation
- Duration caching for performance
- Enhanced error reporting
}
**Configuration System**
- Web interface for most settings
- JSON file validation
- Automatic migration for new settings
- Better error messages and help text
```
**Security Features**
- Input validation and sanitization
- GPIO pin protection (config-file only)
- Rate limiting for API endpoints
- CSRF protection for forms

**Play Scheduling**
- Automatic video playback at set times
- Web interface time picker
- Multiple daily schedules
- Timezone-aware scheduling
**Updated Settings:**
**Night Mode Improvements**
- Configurable start/end times
- Gradual volume reduction
- Visual indicators in web interface
- Holiday schedule overrides

**Performance Optimizations**
- Video duration caching
- Reduced startup time
- Improved memory usage
- Better error recovery

**API Enhancements**
- RESTful endpoint design
- JSON response standardization
- Better status reporting
- Rate limiting implementation
## Version 1.5.0 - June 2025
**Web Interface Launch**
- Modern responsive design
- Video upload functionality
- Real-time status monitoring
- Settings configuration panel

**Monitor Control**
- Automatic HDMI monitor on/off
- GPIO integration for older monitors
- Power management optimization
- Manual override controls
### 🎯 Features
**Video Playback**
- Random start time within video duration
- Better codec support
- Improved error handling
- Volume control integration

**Core Features**
- Random video playback
- GPIO button control
- Basic configuration system
- Video library management
**Play Scheduling**
**Hardware Support**
- Raspberry Pi GPIO integration
- HDMI output control
- USB video source detection
- Physical button interface

**Basic Web Interface**
- Simple control panel
- File upload capability
- Basic status display
- Configuration editing
**Night Mode Improvements**
---

### 🔧 Improvements
### 🔧 Improvements
- Time Format Standardization (HH:MM everywhere)
- Consolidated duplicate time parsing functions
- Enhanced error handling and logging
- Improved type annotations
- Improved file upload handling
- Better format validation
- Duration caching for performance
- Enhanced error reporting
- Video duration caching
- Reduced startup time
- Improved memory usage
- Better error recovery
- RESTful endpoint design
- JSON response standardization
- Better status reporting
- Rate limiting implementation

---
**Performance Optimizations**
### 🐞 Bug Fixes

- Fixed settings form redirect behavior
- Corrected time format validation edge cases
- Improved template rendering for time inputs
**API Enhancements**
---

### 📋 Configuration Schema

**Settings:**
```json
{
  "motion_stop_enabled": false,
  "motion_stop_timeout_seconds": 300,
  "night_mode_start": "22:00",
  "night_mode_end": "06:00",
  "post_playback_cooldown_minutes": 5,
  "button_cooldown_seconds": 60,
  "motion_sensor_enabled": false,
  "motion_sensor_pin": null,
  "enable_statistics": true,
  "statistics_db": "./pawvision_stats.db"
}
```
## Version 1.2.0 - May 2025
---

### Migration Guide
### 🎯 Features
- All features and settings are available in v1.0.0. No migration needed for new users.

---
**Web Interface Launch**
### Known Issues

- Large video files (>2GB) may cause upload timeouts
- Motion sensor requires specific hardware compatibility
- Statistics charts may not display on very old browsers
**Monitor Control**
---

### Upgrade Instructions
### 🔧 Improvements
#### Automatic Update (Recommended)
```bash
curl -sSL https://raw.githubusercontent.com/mkroemer/pawvision/main/install.sh | bash
```

#### Manual Update
```bash
cd /home/pi/PawVision
git pull origin main
pip install -r requirements.txt
sudo systemctl restart pawvision
```
**Video Playback**
---

### Breaking Changes

- Legacy integer time format no longer supported
- Old time parsing methods removed from API
- `timeout_minutes` renamed to `playback_duration_minutes`
- Statistics database schema changed
- API endpoints restructured
## Version 1.0.0 - April 2025
---

### Support
### 🎯 Initial Release
For issues with any version:
- Check [GitHub Issues](https://github.com/mkroemer/PawVision/issues)
- Review [Configuration Guide](configuration.html)
- Consult [API Documentation](api.html)

---
**Core Features**
### Roadmap

#### Upcoming Features (v1.1.0)
- Webhook support for real-time notifications
- Advanced scheduling with recurring patterns
- Video playlist management
- Enhanced motion detection zones
**Hardware Support**
#### Future Considerations
- Mobile app for remote control
- Cloud video storage integration
- Machine learning for pet preference analysis
- Multi-pet support with individual profiles

**Basic Web Interface**


## Migration Guide

### From v2.0.x to v2.1.0

1. **Time Format**: Update any integer time values to HH:MM format
2. **Motion Settings**: Review new motion detection options
3. **Web Interface**: Settings are now organized in cards

### From v1.x to v2.0

1. **Settings Migration**: Run installer to automatically migrate settings
2. **Database**: Statistics will start collecting from scratch
3. **API Changes**: Update any custom integrations for new endpoints
4. **Hardware**: Motion sensor support requires additional GPIO setup

## Known Issues

### Version 2.1.0

### Version 2.0.0

## Upgrade Instructions

### Automatic Update (Recommended)
```bash
curl -sSL https://raw.githubusercontent.com/mkroemer/pawvision/main/install.sh | bash
```

### Manual Update
```bash
cd /home/pi/PawVision
git pull origin main
pip install -r requirements.txt
sudo systemctl restart pawvision
```

## Breaking Changes

### Version 2.1.0

### Version 2.0.0

## Support

For issues with any version:

## Roadmap

### Upcoming Features (v2.2.0)

### Future Considerations
