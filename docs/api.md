# PawVision API Documentation

## Base URL
`http://<raspberry-pi-ip>:5001`

## Authentication
Currently no authentication required. Future versions will support API keys.

---

## Video Control Endpoints

### Play Random Video
Start playing a random video from the library.

**Endpoint:** `POST /api/video/play`

**Request Body:**
```json
{
  "source": "api"  // Optional: "button", "schedule", "api", "motion"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Video playback started",
  "video": "path/to/video.mp4"
}
```

**Status Codes:**
- `200 OK` - Video started successfully
- `400 Bad Request` - No videos available
- `500 Internal Server Error` - Playback failed

---

### Stop Video
Stop the currently playing video.

**Endpoint:** `POST /api/video/stop`

**Response:**
```json
{
  "success": true,
  "message": "Video playback stopped"
}
```

**Status Codes:**
- `200 OK` - Video stopped successfully
- `400 Bad Request` - No video is playing
- `500 Internal Server Error` - Stop failed

---

### Get Video Status
Get current playback status.

**Endpoint:** `GET /api/video/status`

**Response:**
```json
{
  "is_playing": true,
  "current_video": "path/to/video.mp4",
  "start_time": "2025-10-11T14:30:00",
  "elapsed_time": 45.5,
  "next_scheduled_play": "2025-10-11T16:00:00"
}
```

**Status Codes:**
- `200 OK` - Status retrieved successfully

---

## Video Library Endpoints

### Get Video Library
Get all videos in the library.

**Endpoint:** `GET /api/video/library`

**Query Parameters:**
- `type` (optional): Filter by type ("local" or "youtube")

**Response:**
```json
{
  "success": true,
  "videos": [
    {
      "path": "/data/videos/video1.mp4",
      "title": "Custom Title",
      "custom_start_time": 0.0,
      "custom_end_time": null,
      "duration": 300.5,
      "size": 104857600,
      "modified_time": 1633024800.0,
      "is_youtube": false,
      "added_time": "2025-10-11T10:00:00",
      "last_played": "2025-10-11T12:30:00",
      "play_count": 5
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Library retrieved successfully
- `500 Internal Server Error` - Failed to get library

---

### Upload Video
Upload a video file to the library.

**Endpoint:** `POST /api/video/upload`

**Request:** `multipart/form-data`
- `file`: Video file (max 500MB)

**Response:**
```json
{
  "success": true,
  "message": "File 'video.mp4' uploaded successfully",
  "filename": "video.mp4"
}
```

**Status Codes:**
- `200 OK` - Upload successful
- `400 Bad Request` - Invalid file or no file provided
- `413 Payload Too Large` - File exceeds 500MB
- `500 Internal Server Error` - Upload failed

---

### Delete Video
Delete a video from the library.

**Endpoint:** `POST /api/video/delete`

**Request Body:**
```json
{
  "path": "/data/videos/video1.mp4"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Video deleted successfully"
}
```

**Status Codes:**
- `200 OK` - Video deleted successfully
- `400 Bad Request` - No path provided
- `404 Not Found` - Video not found
- `500 Internal Server Error` - Delete failed

---

### Update Video Metadata
Update video title and playback settings.

**Endpoint:** `POST /api/video/update`

**Request Body:**
```json
{
  "path": "/data/videos/video1.mp4",
  "title": "New Custom Title",
  "custom_start_time": 10.0,
  "custom_end_time": 290.0
}
```

**Response:**
```json
{
  "success": true,
  "message": "Video updated successfully"
}
```

**Status Codes:**
- `200 OK` - Video updated successfully
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Video not found
- `500 Internal Server Error` - Update failed

---

## YouTube Integration Endpoints

### Add YouTube Video
Add a YouTube video to the library.

**Endpoint:** `POST /api/youtube/add`

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "title": "Custom Title",
  "quality": "720p",
  "download": false,
  "custom_start_time": 0.0,
  "custom_end_offset": 10.0
}
```

**Response:**
```json
{
  "success": true,
  "message": "YouTube video added successfully",
  "video": {
    "path": "youtube://VIDEO_ID",
    "title": "Custom Title",
    "duration": 300.0
  }
}
```

**Status Codes:**
- `200 OK` - Video added successfully
- `400 Bad Request` - Invalid URL or parameters
- `500 Internal Server Error` - Failed to add video

---

### Download YouTube Video
Download a YouTube video for offline playback.

**Endpoint:** `POST /api/youtube/download`

**Request Body:**
```json
{
  "path": "youtube://VIDEO_ID",
  "quality": "720p"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Download started",
  "download_id": "abc123"
}
```

**Status Codes:**
- `200 OK` - Download started
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Video not found
- `500 Internal Server Error` - Download failed

---

### Get Download Progress
Get progress of a YouTube video download.

**Endpoint:** `GET /api/youtube/download/progress/{download_id}`

**Response:**
```json
{
  "success": true,
  "progress": {
    "status": "downloading",
    "percent": 45.5,
    "speed": "2.5 MB/s",
    "eta": "30s"
  }
}
```

**Status Codes:**
- `200 OK` - Progress retrieved
- `404 Not Found` - Download ID not found

---

## Configuration Endpoints

### Get Configuration
Get current configuration.

**Endpoint:** `GET /api/config`

**Response:**
```json
{
  "success": true,
  "config": {
    "playback_duration_minutes": 30,
    "post_playback_cooldown_minutes": 5,
    "volume": 50,
    "night_mode_start": "22:00",
    "night_mode_end": "06:00",
    "button_enabled": true,
    "enable_statistics": true
  }
}
```

**Status Codes:**
- `200 OK` - Configuration retrieved successfully

---

### Update Configuration
Update configuration settings.

**Endpoint:** `POST /api/config`

**Request Body:**
```json
{
  "playback_duration_minutes": 45,
  "volume": 60,
  "night_mode_start": "23:00"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration updated successfully",
  "config": { /* updated config */ }
}
```

**Status Codes:**
- `200 OK` - Configuration updated successfully
- `400 Bad Request` - Invalid parameters
- `500 Internal Server Error` - Update failed

---

## Statistics Endpoints

### Get Statistics Summary
Get summary statistics.

**Endpoint:** `GET /api/statistics/summary`

**Response:**
```json
{
  "success": true,
  "statistics": {
    "total_button_presses": 150,
    "total_videos_played": 450,
    "total_playback_time": 13500.0,
    "average_session_length": 30.0,
    "most_played_video": "/data/videos/favorite.mp4",
    "peak_usage_hour": "14:00"
  }
}
```

**Status Codes:**
- `200 OK` - Statistics retrieved successfully
- `500 Internal Server Error` - Failed to get statistics

---

### Get Recent Activity
Get recent system events.

**Endpoint:** `GET /api/statistics/activity`

**Query Parameters:**
- `limit` (optional): Number of events to return (default: 50, max: 500)
- `type` (optional): Filter by event type

**Response:**
```json
{
  "success": true,
  "activity": [
    {
      "timestamp": "2025-10-11T14:30:00",
      "event_type": "video_playback",
      "action": "started",
      "video_file": "/data/videos/video1.mp4",
      "source": "button"
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Activity retrieved successfully
- `500 Internal Server Error` - Failed to get activity

---

## Hardware Control Endpoints

### Simulate Button Press
Trigger a button press programmatically (dev mode only).

**Endpoint:** `POST /api/button/press`

**Response:**
```json
{
  "success": true,
  "message": "Button press simulated"
}
```

**Status Codes:**
- `200 OK` - Button press triggered
- `403 Forbidden` - Not in dev mode
- `500 Internal Server Error` - Failed to trigger

---

## Error Responses

All error responses follow this format:

```json
{
  "success": false,
  "message": "Error description",
  "error": "Detailed error information (optional)"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. Future versions will include:
- 100 requests per minute per IP
- 1000 requests per hour per IP

---

## WebSocket Support (Future)

Future versions will support WebSocket connections for real-time updates:

**Endpoint:** `ws://<raspberry-pi-ip>:5001/ws`

**Events:**
- `video.started`
- `video.stopped`
- `button.pressed`
- `config.updated`
- `statistics.updated`

---

## Home Assistant Integration

PawVision can be integrated with Home Assistant using REST commands.

### Example Configuration

```yaml
# configuration.yaml
rest_command:
  pawvision_play:
    url: "http://192.168.1.100:5001/api/video/play"
    method: POST
    content_type: "application/json"
    payload: '{"source": "automation"}'
  
  pawvision_stop:
    url: "http://192.168.1.100:5001/api/video/stop"
    method: POST

switch:
  - platform: template
    switches:
      pawvision:
        friendly_name: "Pet TV"
        value_template: "{{ is_state('sensor.pawvision_status', 'playing') }}"
        turn_on:
          service: rest_command.pawvision_play
        turn_off:
          service: rest_command.pawvision_stop

sensor:
  - platform: rest
    name: pawvision_status
    resource: http://192.168.1.100:5001/api/video/status
    json_attributes:
      - is_playing
      - current_video
      - elapsed_time
    value_template: "{{ 'playing' if value_json.is_playing else 'stopped' }}"
    scan_interval: 30
```

---

## Version

Current API Version: 2.0.0

Last Updated: October 11, 2025
