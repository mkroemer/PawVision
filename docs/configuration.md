layout: pawvision-theme
title: Configuration Guide
permalink: /configuration/

Complete setup and configuration guide for your PawVision Pet TV system.

## Installation

### Quick Install

Run this one-liner on your Raspberry Pi:

```bash
curl -sSL https://raw.githubusercontent.com/mkroemer/pawvision/main/install.sh | bash
```

This installer will:
- Install all required dependencies
- Download the latest PawVision version
- Preserve your existing videos and settings
- Merge new configuration options automatically

### Manual Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mkroemer/PawVision.git
   cd PawVision
   ```

2. **Install dependencies**:
   ```bash
   ```

3. **Run PawVision**:
   python pawvision.py
   ```

## Web Interface
- **Comprehensive settings** all in one place

## Configuration Options

### Video Settings

| Setting | Description | Range | Default |
|---------|-------------|--------|---------|
| **Playback Duration** | How long videos play | 1-180 minutes | 30 minutes |
| **Post-Playback Cooldown** | Delay before next video | 0-60 minutes | 5 minutes |
| **Volume** | Audio volume level | 0-100 | 50 |

```json
{
  "playback_duration_minutes": 30,
  "post_playback_cooldown_minutes": 5,
  "volume": 50
}
```

### Night Mode Settings

Configure quiet hours when volume is muted:

| Setting | Description | Format | Default |
|---------|-------------|--------|---------|
| **Night Mode Start** | When quiet hours begin | HH:MM | 22:00 |
| **Night Mode End** | When quiet hours end | HH:MM | 06:00 |

```json
{
  "night_mode_start": "22:00",
  "night_mode_end": "06:00"
}
```

### Button Control Settings

Physical GPIO button configuration:

| Setting | Description | Default |
|---------|-------------|---------|
| **Button Enabled** | Enable/disable physical button | true |
| **Second Press Stops** | Allow button to stop video | true |
| **Button Cooldown** | Seconds between button presses | 60 |
| **Disable Start Time** | When to disable button (optional) | null |
| **Disable End Time** | When to re-enable button (optional) | null |

```json
{
  "button_enabled": true,
  "button_disable_start": "23:30",
  "button_disable_end": "06:00",
  "second_press_stops": true,
  "button_cooldown_seconds": 60
}
```

### Motion Detection Settings

Optional motion sensor integration:

| Setting | Description | Default |
|---------|-------------|---------|
{
  "motion_sensor_enabled": false,
  "motion_stop_enabled": false,
  "motion_stop_timeout_seconds": 300
}
```

### Hardware Settings (Config File Only)

These settings are only configurable in the JSON file for security:

| Setting | Description | Default |
|---------|-------------|---------|
| **Monitor GPIO** | GPIO pin for monitor control | null |
| **Button Pin** | GPIO pin for physical button | 17 |
| **Motion Sensor Pin** | GPIO pin for motion sensor | null |

```json
{
  "monitor_gpio": null,
  "button_pin": 17,
  "motion_sensor_pin": 18
}
```

### Play Schedule

Set up automatic playback times:

```json
{
  "play_schedule": ["08:00", "12:00", "16:00", "20:00"]
}
```

Use the web interface time picker to easily add/remove scheduled times.

### Statistics Settings

Track your pet's viewing patterns:

```json
{
  "enable_statistics": true,
  "statistics_file": "./pawvision_stats.json",
  "statistics_db": "./pawvision_stats.db"
}
```

## Web Interface vs Config File

### ✅ Configurable via Web Interface
- Playback duration and cooldown
- Volume and night mode settings
- Button enable/disable and scheduling
- Motion sensor enable/disable
- Play schedule management

### ❌ Config File Only
- GPIO pin assignments (for security)
- File paths and database locations
- Advanced hardware settings

## Video Management

### Default Video Location
Place videos in:
```
/home/pi/videos/
```

### USB Support
Plug in a USB stick - it will be auto-mounted to `/media/usb` and videos will be detected automatically.

### Supported Formats
- MP4, AVI, MKV, MOV, WMV
- Most common video codecs
- Automatic duration detection with caching

## Monitor Control

PawVision automatically controls your HDMI monitor:

- **Turns ON** when video playback starts
- **Turns OFF** when video stops (timeout, manual stop, or button press)
- **GPIO Control** optional via `monitor_gpio` setting
- **No manual control needed** - it's all automatic!

## API Integration

### REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/play` | POST | Start video playback |
| `/api/stop` | POST | Stop video playback |
| `/api/status` | GET | Get current status |

### Home Assistant Example

```yaml
rest_command:
  pawvision_play:
    url: "http://192.168.1.50:5001/api/play"
    method: POST
  pawvision_stop:
    url: "http://192.168.1.50:5001/api/stop"
    method: POST
```

## Best Practices

### Hardware Setup
- **GPIO Pins**: Choose pins that don't conflict with other devices
- **Motion Sensor**: Place at pet's eye level for best detection
- **Button Placement**: Mount where your pet can easily access

### Configuration Tips
- **Cooldown Periods**: Set appropriate delays to prevent over-triggering
- **Night Mode**: Align with your household's sleep schedule
- **Motion Timeout**: Start with 5 minutes, adjust based on pet behavior
- **Video Duration**: Start with 15-30 minutes, adjust based on attention span

### Maintenance
- **Regular Updates**: Run the installer periodically for updates
- **Video Rotation**: Add new videos regularly to keep pets engaged
- **Statistics Review**: Check viewing patterns to optimize settings
- **Backup Settings**: Keep a copy of your `pawvision_settings.json`

## Troubleshooting

### Common Issues

**Button Not Responding**
- Check GPIO pin assignment in config
- Verify physical wiring
- Check if button is disabled by schedule
- Look for cooldown period messages

**Motion Sensor Not Working**
- Verify `motion_sensor_enabled` is true
- Check GPIO pin wiring
- Ensure motion sensor has proper power
- Test placement and sensitivity

**Web Interface Not Accessible**
- Check if PawVision is running: `systemctl status pawvision`
- Verify port 5001 is not blocked by firewall
- Check network connectivity to Raspberry Pi

**Videos Not Playing**
- Verify video files are in `/home/pi/videos/`
- Check video format compatibility
- Look for errors in logs: `journalctl -u pawvision`

### Log Messages

Common log messages and their meanings:

- `DEV_MODE: GPIO button disabled` - Normal in development mode
- `Motion sensor disabled in configuration` - Motion sensor not enabled
- `Button press blocked by cooldown period` - Cooldown protection active
- `Motion lost - stopping video playback` - Motion sensor triggered stop
- `Night mode active, muting volume` - Night mode engaged

### Getting Help

For additional support:
- Check the [GitHub Issues](https://github.com/mkroemer/PawVision/issues)
- Review the [Release Notes](releases.html) for recent changes
- Join discussions in the repository

## Example Configurations

### Basic Setup
```json
{
  "playback_duration_minutes": 15,
  "volume": 75,
  "night_mode_start": "22:00",
  "night_mode_end": "07:00",
  "button_enabled": true
}
```

### Advanced Setup with Motion Detection
```json
{
  "playbook_duration_minutes": 30,
  "post_playback_cooldown_minutes": 2,
  "volume": 60,
  "night_mode_start": "21:30",
  "night_mode_end": "07:30",
  "button_enabled": true,
  "button_disable_start": "23:00",
  "button_disable_end": "07:00",
  "motion_sensor_enabled": true,
  "motion_stop_enabled": true,
  "motion_stop_timeout_seconds": 300,
  "play_schedule": ["08:00", "14:00", "19:00"]
}
```

## 🧪 Running and Writing Tests

PawVision uses [pytest](https://docs.pytest.org/) for all unit and integration tests. All test files are located in the `tests/` directory and are organized by domain (e.g., config, statistics, web interface).

To run all tests:

```bash
python run_tests.py --all
```

To run a specific test file:

```bash
python run_tests.py --file tests/test_config.py
```

To run a specific test class:

```bash
python run_tests.py --class TestConfigManager
```

To run a specific test class in a file:

```bash
python run_tests.py --file tests/test_config.py --class TestConfigManager
```

- Place new tests in the appropriate domain file in `tests/`
- Use the `unittest` framework (pytest will auto-discover)
- Test files should be named `test_*.py`
- Use temporary files and directories for isolation
- Mock hardware and external dependencies for reliability

All tests should pass before submitting changes. Logging errors during test shutdown are harmless and only occur in test environments.
