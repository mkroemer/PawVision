# Video Library Management Feature

## Overview

PawVision now includes a comprehensive video library management system that allows you to customize playback for each video. You can define custom start times, end times, and titles for each video in your collection.

## Key Features

### Custom Start and End Times
- **Start Time**: Define where each video should begin playing (skip intros, logos, etc.)
- **End Time**: Define where each video should stop playing (skip credits, outtros, etc.)
- **Default Values**: Start time defaults to 0 seconds, end time defaults to the full video duration

### Custom Video Titles
- **Optional Titles**: Give each video a friendly name that's more descriptive than the filename
- **Display**: The web interface shows the custom title prominently, with the filename as a subtitle

### Smart Playback
- **Effective Duration**: The system calculates the actual playable duration considering your custom range
- **Random Start Points**: When playing videos, the system randomly selects start points within your custom range
- **Time Compliance**: All timing settings (timeout, random selection) respect your custom start/end times

## How It Works

### Video Library Database
- PawVision automatically creates a SQLite database (`pawvision_library.db`) to store metadata
- The database syncs with your video files on startup and when accessing the playlist
- Deleted files are automatically removed from the library
- Modified files are automatically updated with new duration/size information

### File System Integration
- The library automatically discovers all video files in your configured directories
- Supported formats: MP4, MKV, AVI, MOV, M4V, WEBM
- Videos are automatically added to the library when first detected
- File metadata (size, modification time, duration) is cached for performance

## Using the Feature

### Web Interface

1. **Viewing Videos**: Go to the "Playlist" tab to see your video library
   - Videos show their display title (custom title or filename)
   - File information includes size, duration, and effective duration
   - Custom time ranges are highlighted in blue

2. **Editing Video Settings**: Click the "Edit" button next to any video
   - **Custom Title**: Enter a friendly name (leave empty to use filename)
   - **Start Time**: Set start point in seconds (e.g., 30 to skip first 30 seconds)
   - **End Time**: Set end point in seconds (leave empty for full duration)
   - Changes are saved immediately and applied to future playback

### Video Playback

When a video is selected for playback:

1. **Range Validation**: The system uses your custom start/end times
2. **Duration Check**: Compares available duration with configured playback timeout
3. **Random Selection**: 
   - If your custom range is longer than the timeout, a random start point is chosen within the range
   - If your custom range is shorter than the timeout, the entire range is played
4. **Playback**: Video starts at the calculated time and respects your end time

### Example Use Cases

#### Skipping Intro/Outro
```
Video: "pet_birds_documentary.mp4" (Duration: 3600 seconds / 1 hour)
Custom Title: "Beautiful Birds Documentary"
Start Time: 45 seconds (skip intro)
End Time: 3540 seconds (skip credits)
Effective Duration: 3495 seconds (~58 minutes)
```

#### Creating Highlight Reels
```
Video: "long_nature_video.mp4" (Duration: 7200 seconds / 2 hours)  
Custom Title: "Best Nature Moments"
Start Time: 1800 seconds (30 minutes in)
End Time: 3600 seconds (1 hour in)
Effective Duration: 1800 seconds (30 minutes of highlights)
```

#### Pet-Safe Content
```
Video: "mixed_content.mp4" (Duration: 1800 seconds / 30 minutes)
Custom Title: "Safe Pet Content"
Start Time: 300 seconds (skip loud opening)
End Time: 1500 seconds (skip scary ending)
Effective Duration: 1200 seconds (20 minutes safe content)
```

## Technical Details

### Database Schema
```sql
CREATE TABLE video_library (
    path TEXT PRIMARY KEY,           -- Full file path
    title TEXT,                      -- Custom title (optional)
    custom_start_time REAL,          -- Start time in seconds
    custom_end_time REAL,            -- End time in seconds (NULL = full duration)
    duration REAL,                   -- Total video duration
    size INTEGER,                    -- File size in bytes
    modified_time REAL,              -- File modification timestamp
    created_at TEXT,                 -- When library entry was created
    updated_at TEXT                  -- When library entry was last updated
);
```

### API Integration

The library integrates seamlessly with existing PawVision APIs:
- Button presses use the new video selection system
- Scheduled playback respects custom ranges
- Home Assistant API calls work with the enhanced video player
- Statistics tracking continues to work with custom titles and ranges

### Configuration

The video library database path can be configured in `pawvision_settings.json`:
```json
{
  "library_db_path": "/home/pi/pawvision_library.db"
}
```

Default paths:
- **Production**: `/home/pi/pawvision_library.db`
- **Development**: `./pawvision_library.db`

### Backup and Migration

#### Export Library
```python
from pawvision.video_library import VideoLibraryManager
library = VideoLibraryManager()
library.export_to_json("my_library_backup.json")
```

#### Import Library  
```python
from pawvision.video_library import VideoLibraryManager
library = VideoLibraryManager()
success, count = library.import_from_json("my_library_backup.json")
```

## Migration from Previous Versions

- **Existing Videos**: All existing videos are automatically added to the library with default settings
- **No Data Loss**: Original video files are never modified
- **Backward Compatibility**: Videos without custom settings work exactly as before
- **Gradual Adoption**: You can edit videos one at a time as needed

## Performance

- **Caching**: Video durations and metadata are cached for fast loading
- **Sync Optimization**: Only modified files are re-processed during sync
- **Database Indexing**: Optimized queries for fast video lookup
- **Memory Efficient**: Metadata is loaded on-demand, videos are not kept in memory

## Troubleshooting

### Common Issues

1. **Videos Not Appearing**: Check that video files are in configured directories
2. **Duration Not Detected**: Ensure `mediainfo` is installed on your system
3. **Custom Times Not Saving**: Verify database file permissions
4. **Performance Issues**: Try clearing the cache from dev tools or restart PawVision

### Logging

Video library operations are logged at DEBUG level:
```
pawvision.video_library - INFO - Video library database initialized
pawvision.video_library - DEBUG - Added new video entry: video.mp4
pawvision.video_library - DEBUG - Updated video entry: video.mp4
```

This powerful new feature gives you complete control over your pet's video experience while maintaining the simplicity and reliability that makes PawVision special!
