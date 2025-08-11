# PawVision API Documentation

## Overview

PawVision provides a RESTful API for managing video playback, file operations, and system configuration. All API endpoints return JSON responses and follow REST conventions.

## Base URL

```
http://localhost:5001
```

## API Endpoints

### Video Management

#### Upload Video
- **POST** `/api/video/upload`
- **Content-Type:** `multipart/form-data`
- **Body:** File upload with `file` field
- **Response:** `{"success": "Uploaded {filename}"}` or error
- **Description:** Upload a video file to the video library

#### Delete Video
- **POST** `/api/video/delete`
- **Content-Type:** `application/x-www-form-urlencoded`
- **Body:** `path={video_path}`
- **Response:** `{"success": "Deleted {filename}"}` or error
- **Description:** Delete a video file or YouTube video from library

#### Update Video Metadata
- **POST** `/api/video/update`
- **Content-Type:** `application/x-www-form-urlencoded`
- **Body:**
  ```
  path={video_path}
  title={custom_title}
  custom_start_time={start_seconds}
  custom_end_offset={end_offset_seconds}
  ```
- **Response:** Redirect to `/#playlist` or error
- **Description:** Update video title and playback range

### YouTube Operations

#### Add YouTube Video
- **POST** `/api/youtube/add`
- **Content-Type:** `application/json`
- **Body:**
  ```json
  {
    "url": "https://youtube.com/watch?v=...",
    "title": "Custom Title (optional)",
    "quality": "720p",
    "start_time": 0,
    "end_time": null,
    "download": false
  }
  ```
- **Response:** `{"status": "success", "message": "YouTube video added successfully"}` or error
- **Description:** Add a YouTube video to the library

#### Validate YouTube URL
- **POST** `/api/youtube/validate`
- **Content-Type:** `application/json`
- **Body:**
  ```json
  {
    "url": "https://youtube.com/watch?v=..."
  }
  ```
- **Response:**
  ```json
  {
    "valid": true,
    "title": "Video Title",
    "duration": 300
  }
  ```
- **Description:** Validate YouTube URL and fetch metadata

#### Download YouTube Video
- **POST** `/api/youtube/download`
- **Content-Type:** `application/json`
- **Body:**
  ```json
  {
    "path": "youtube://video_id",
    "quality": "720p"
  }
  ```
- **Response:** `{"status": "started", "download_id": "video_id"}` or error
- **Description:** Start downloading YouTube video for offline playback

#### Get Download Progress
- **GET** `/api/youtube/download/progress/{download_id}`
- **Response:**
  ```json
  {
    "status": "downloading",
    "percentage": 45,
    "video_title": "Video Title"
  }
  ```
- **Description:** Get download progress for a specific video

#### Refresh YouTube Streams
- **POST** `/api/youtube/refresh`
- **Response:** `{"status": "success", "refreshed": 5}` or error
- **Description:** Refresh expired YouTube stream URLs

### Playback Control

#### Start Playback
- **POST** `/api/play`
- **Response:** `{"status": "playing"}` or error
- **Description:** Start playing a random video

#### Stop Playback
- **POST** `/api/stop`
- **Response:** `{"status": "stopped"}` or error
- **Description:** Stop current video playback

#### Get Status
- **GET** `/api/status`
- **Response:**
  ```json
  {
    "is_playing": false,
    "button_allowed": true,
    "next_scheduled_play": "2025-08-11T15:30:00",
    "night_mode": false,
    "video_count": 12
  }
  ```
- **Description:** Get current system status

#### Health Check
- **GET** `/api/health`
- **Response:**
  ```json
  {
    "status": "healthy",
    "version": "2.0.0",
    "timestamp": "2025-08-11T10:30:00",
    "is_playing": false,
    "video_count": 12,
    "stats": {
      "total_button_presses": 156,
      "total_video_plays": 89,
      "total_api_calls": 245
    }
  }
  ```
- **Description:** System health and status information

### Statistics

#### Get Statistics Summary
- **GET** `/api/statistics`
- **Response:**
  ```json
  {
    "status": "success",
    "statistics": {
      "total_button_presses": 156,
      "today_button_presses": 8,
      "daily_average": 22.3,
      "peak_hour": "14:00",
      "total_viewing_minutes": 1240,
      "yesterday_viewing_minutes": 67
    }
  }
  ```
- **Description:** Get detailed usage statistics

#### Get Hourly Statistics
- **GET** `/api/statistics/hourly?date=2025-08-11`
- **Response:**
  ```json
  {
    "status": "success",
    "date": "2025-08-11",
    "hourly_data": {
      "00": 0,
      "01": 0,
      "14": 5,
      "15": 3
    }
  }
  ```
- **Description:** Get hourly usage data for a specific date

#### Clear Statistics
- **POST** `/api/statistics/clear`
- **Response:** `{"status": "success", "message": "Statistics cleared"}` or error
- **Description:** Clear all usage statistics

### Settings Management

#### Update Settings
- **POST** `/settings`
- **Content-Type:** `application/x-www-form-urlencoded`
- **Body:** Form data with configuration parameters
- **Response:** Redirect to main page or error
- **Description:** Update system configuration

### Development Endpoints

*Available only when `dev_mode` is enabled*

#### Simulate Button Press
- **GET** `/dev/button`
- **Response:** `{"success": "Button press simulated"}` or error
- **Description:** Simulate physical button press for testing

#### Clear Cache
- **GET** `/dev/cache/clear`
- **Response:** `{"success": "Cache cleared"}` or error
- **Description:** Clear video duration cache

## UI Routes

### Main Interface
- **GET** `/`
- **Response:** HTML page with video library and controls
- **Description:** Main dashboard interface

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200` - Success
- `400` - Bad Request (validation errors)
- `404` - Not Found
- `409` - Conflict (e.g., file already exists)
- `413` - Payload Too Large (file upload)
- `500` - Internal Server Error

Error responses include a JSON object with an `error` field:

```json
{
  "error": "Description of the error"
}
```

## Data Formats

### Video Quality Options
- `360p`
- `480p`
- `720p` (default)
- `1080p`

### Time Format
- All time values are in seconds (float)
- Negative values are not allowed for start times
- End times must be greater than start times

### Video Paths
- Regular videos: Full file path (e.g., `/path/to/video.mp4`)
- YouTube videos: `youtube://video_id` format

## Rate Limiting

Currently no rate limiting is implemented, but it's recommended for production deployments.

## Authentication

No authentication is currently implemented. The API is designed for local network use.

## WebSocket Events

Currently not implemented, but planned for real-time updates.

## Examples

### Add a YouTube Video with Custom Range

```bash
curl -X POST http://localhost:5001/api/youtube/add \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "title": "Never Gonna Give You Up",
    "quality": "720p",
    "start_time": 10,
    "end_time": 60,
    "download": true
  }'
```

### Upload a Video File

```bash
curl -X POST http://localhost:5001/api/video/upload \
  -F "file=@/path/to/video.mp4"
```

### Start Video Playback

```bash
curl -X POST http://localhost:5001/api/play
```

### Get System Status

```bash
curl http://localhost:5001/api/status
```

## Client Libraries

Currently no official client libraries exist, but the API follows standard REST conventions making it easy to integrate with any HTTP client.
