---
layout: pawvision-theme
title: API Reference
---

RESTful API endpoints for controlling PawVision programmatically.

## Base URL

```
http://<raspberry-pi-ip>:5001
```

## Authentication

No authentication required for local network access.

## Endpoints

### Video Control

#### Start Video Playback

```http
POST /api/play
```

Starts random video playback from the video library.

**Response:**
```json
{
  "status": "playing"
}
```

**Status Codes:**
- `200 OK` - Video started successfully
- `409 Conflict` - Video already playing
- `500 Internal Server Error` - Failed to start playback

#### Stop Video Playback

```http
POST /api/stop
```

Stops current video playback and turns off monitor.

**Response:**
```json
{
  "status": "stopped"
}
```

**Status Codes:**
- `200 OK` - Video stopped successfully
- `404 Not Found` - No video currently playing
- `500 Internal Server Error` - Failed to stop playback

### Status Information

#### Get Current Status

```http
GET /api/status
```

Returns current system status and configuration.

**Response:**
```json
{
  "is_playing": true,
  "current_video": "cute_cat_video.mp4",
  "remaining_time": 1250,
  "volume": 50,
  "night_mode_active": false,
  "button_enabled": true,
  "motion_sensor_enabled": true,
  "last_motion_detected": "2024-08-10T14:30:22Z"
}
```

#### Get Video Library

```http
GET /api/videos
```

Returns list of available videos with metadata.

**Response:**
```json
{
  "videos": [
    {
      "filename": "cat_compilation.mp4",
      "duration": 1800,
      "size": 45678912,
      "last_played": "2024-08-10T12:15:30Z"
    }
  ],
  "total_count": 12,
  "total_duration": 21600
}
```

### Statistics

#### Get Usage Statistics
{
  "total_sessions": 45,
  "daily_stats": {
    "2024-08-10": {
    }
}
```

#### Get Detailed Statistics
Returns comprehensive statistics with hourly breakdowns.

**Response:**
```json
{
  "summary": {
    "total_sessions": 45,
    "unique_videos_played": 8
  },
  "hourly_distribution": {
    "08": 5,
    "14": 12,
    "20": 8
  },
  "video_performance": [
    {
      "filename": "bird_watching.mp4",
      "play_count": 12,
      "total_watch_time": 4500,
      "average_completion": 0.85
    }
  ],
  "end_reasons": {
    "timeout": 25,
    "manual_stop": 15,
    "motion_sensor": 5
  }
}
```

## Integration Examples

### Home Assistant

Add these to your `configuration.yaml`:

```yaml
rest_command:
  pawvision_play:
    url: "http://192.168.1.50:5001/api/play"
    method: POST
    
  pawvision_stop:
    url: "http://192.168.1.50:5001/api/stop"
    method: POST

sensor:
  - platform: rest
    resource: "http://192.168.1.50:5001/api/status"
    name: "PawVision Status"
    value_template: "{{ value_json.is_playing }}"
    json_attributes:
      - current_video
      - remaining_time
      - volume
      - night_mode_active

automation:
  - alias: "Pet TV Morning Schedule"
    trigger:
      platform: time
      at: "08:00:00"
    action:
      service: rest_command.pawvision_play
```

### Node.js/JavaScript

```javascript
const PAWVISION_URL = 'http://192.168.1.50:5001';

async function playVideo() {
  try {
    const response = await fetch(`${PAWVISION_URL}/api/play`, {
      method: 'POST'
    });
    const result = await response.json();
    console.log('Video started:', result);
  } catch (error) {
    console.error('Failed to start video:', error);
  }
}

async function getStatus() {
  try {
    const response = await fetch(`${PAWVISION_URL}/api/status`);
    const status = await response.json();
    console.log('Current status:', status);
    return status;
  } catch (error) {
    console.error('Failed to get status:', error);
  }
}

// Check if video is playing
const status = await getStatus();
if (status.is_playing) {
  console.log(`Playing: ${status.current_video}`);
} else {
  console.log('No video playing');
}
```

### Python

```python
import requests
import json

PAWVISION_URL = 'http://192.168.1.50:5001'

def play_video():
    try:
        response = requests.post(f'{PAWVISION_URL}/api/play')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Failed to start video: {e}')
        return None

def get_stats():
    try:
        response = requests.get(f'{PAWVISION_URL}/api/stats')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Failed to get statistics: {e}')
        return None

# Example usage
result = play_video()
if result:
    print(f"Video started: {result['status']}")

stats = get_stats()
if stats:
    print(f"Total sessions: {stats['total_sessions']}")
    print(f"Total viewing time: {stats['total_viewing_time']} seconds")
```

### curl Examples

```bash
# Start video playback
curl -X POST http://192.168.1.50:5001/api/play

# Stop video playback
curl -X POST http://192.168.1.50:5001/api/stop

# Get current status
curl http://192.168.1.50:5001/api/status

# Get statistics
curl http://192.168.1.50:5001/api/stats

# Get video library
curl http://192.168.1.50:5001/api/videos
```

## Error Handling

All API endpoints return appropriate HTTP status codes:

- `200 OK` - Request successful
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `409 Conflict` - Request conflicts with current state
- `500 Internal Server Error` - Server error

Error responses include a JSON body with details:

```json
{
  "error": "Video already playing",
  "code": "VIDEO_ALREADY_PLAYING",
  "timestamp": "2024-08-10T14:30:22Z"
}
```

## Rate Limiting

API calls are limited to prevent abuse:
- Maximum 60 requests per minute per IP
- Playback commands have additional cooldown periods
- Statistics endpoints are cached for 30 seconds

## Best Practices

1. **Check Status First**: Before starting playback, check if video is already playing
2. **Handle Errors**: Always check response status codes and handle errors gracefully
3. **Use Appropriate Intervals**: Don't poll status endpoints too frequently
4. **Respect Cooldowns**: Honor the button cooldown settings in automated scripts
5. **Monitor Statistics**: Use stats endpoints to understand usage patterns

## Webhooks (Future)

Webhook support is planned for future releases to enable real-time notifications:
- Video start/stop events
- Motion detection events
- System status changes
- Error notifications

Stay tuned for updates in future releases!
