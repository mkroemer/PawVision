"""
CODEBASE REFACTORING ANALYSIS
==============================

Date: October 11, 2025
Context: After successfully splitting web_interface.py (1,272 → 159 lines)

FILE SIZE ANALYSIS
==================

Current state of pawvision/ directory:

🔴 LARGE FILES (500+ lines):
  - video_player.py          631 lines  ⚠️ SHOULD SPLIT
  - database.py              561 lines  ✅ OK (well-organized)

🟡 MEDIUM FILES (350-500 lines):
  - youtube_manager.py       492 lines  📋 CONSIDER SPLITTING
  - statistics.py            459 lines  ✅ OK (single responsibility)
  - security.py              387 lines  ✅ OK (well-organized)

🟢 ACCEPTABLE FILES (<350 lines):
  - main.py                  336 lines  ✅ OK (entry point)
  - gpio_handler.py          316 lines  ✅ OK (single responsibility)
  - config.py                248 lines  ✅ OK
  - video_library.py         235 lines  ✅ OK
  - logging_config.py        226 lines  ✅ OK
  - web_interface.py         159 lines  ✅ JUST REFACTORED!
  - time_utils.py            131 lines  ✅ OK

================================================================================
RECOMMENDATION 1: Split video_player.py (HIGH PRIORITY)
================================================================================

Current Structure:
------------------
video_player.py (631 lines) contains:
  ✓ VideoPlayer class initialization (lines 1-100)
  ✓ Monitor control (GPIO relay management)
  ✓ Video library syncing
  ✓ Playback control (play, stop, pause)
  ✓ Process management (omxplayer, vlc, mpv)
  ✓ Duration probing (mediainfo, ffprobe)
  ✓ Video format detection
  ✓ Statistics recording
  ✓ Timeout management
  ✓ Library entry management

Problems:
---------
  ❌ Too many responsibilities (violates Single Responsibility Principle)
  ❌ Hard to test individual components
  ❌ Mixing player backends with utility functions
  ❌ Difficult to add new player backends
  ❌ Duration probing mixed with playback logic

Proposed Split:
---------------

1. video_player.py (~200 lines)
   - VideoPlayer class (main interface)
   - High-level playback control
   - Video library integration
   - Statistics recording
   - Public API methods

2. playback/
   ├── __init__.py
   ├── engine.py (~150 lines)
   │   - PlaybackEngine base class
   │   - Process management
   │   - Player backend selection
   │   - Timeout management
   │
   ├── backends.py (~150 lines)
   │   - OMXPlayerBackend
   │   - VLCBackend
   │   - MPVBackend
   │   - Backend detection/selection
   │
   └── video_utils.py (~150 lines)
       - get_video_duration()
       - detect_video_format()
       - validate_video_file()
       - Video file utilities

Benefits:
---------
  ✅ Each file has single, clear purpose
  ✅ Easy to add new player backends
  ✅ Better testability
  ✅ Clearer code organization
  ✅ Easier to maintain
  ✅ Can test video utilities independently

Migration Impact: MEDIUM
  - Update imports in main.py
  - Update imports in web interface blueprints
  - No API changes needed

================================================================================
RECOMMENDATION 2: Split youtube_manager.py (MEDIUM PRIORITY)
================================================================================

Current Structure:
------------------
youtube_manager.py (492 lines) contains:
  ✓ YouTubeManager class
  ✓ Video ID extraction
  ✓ Timestamp extraction from URLs
  ✓ Video info fetching (yt-dlp)
  ✓ Stream URL generation
  ✓ Video downloading with progress
  ✓ VideoEntry creation
  ✓ Stream refresh logic
  ✓ Download cleanup

Problems:
---------
  ⚠️ Mixes extraction with downloading
  ⚠️ Large class with many methods
  ⚠️ Could benefit from separation of concerns

Proposed Split:
---------------

1. youtube_manager.py (~200 lines)
   - YouTubeManager main class
   - Public API methods
   - VideoEntry creation
   - Stream refresh coordination

2. youtube/
   ├── __init__.py
   ├── extractor.py (~150 lines)
   │   - extract_video_id()
   │   - extract_timestamp_from_url()
   │   - get_video_info()
   │   - get_stream_url()
   │
   └── downloader.py (~150 lines)
       - download_video()
       - progress tracking
       - cleanup_expired_downloads()

Benefits:
---------
  ✅ Clearer separation of read vs write operations
  ✅ Easier to test extraction separately
  ✅ Can mock downloader in tests
  ✅ Better organization

Migration Impact: LOW
  - Only internal to youtube_manager
  - No external API changes

================================================================================
RECOMMENDATION 3: Keep database.py As-Is (NO ACTION)
================================================================================

Current Structure:
------------------
database.py (561 lines) contains:
  ✓ VideoEntry dataclass (~200 lines)
  ✓ DatabaseManager class (~200 lines)
  ✓ Database initialization
  ✓ Migration logic
  ✓ CRUD operations

Analysis:
---------
  ✅ Well-organized with clear classes
  ✅ Good separation between model and manager
  ✅ Single responsibility (database operations)
  ✅ Easy to understand
  ✅ Migrations are isolated

VERDICT: Keep as-is
  - File is large but well-structured
  - Clear separation of concerns within file
  - Would only split if adding many more models
  - Current structure follows good patterns

Alternative (if needed later):
-------------------------------
Could split into:
  - models/video_entry.py
  - database_manager.py
  - migrations.py

But this is NOT needed now.

================================================================================
PRIORITY RANKING
================================================================================

1. 🔴 HIGH PRIORITY: video_player.py
   - Immediate benefit from splitting
   - Will improve testability significantly
   - Clear separation of concerns
   - Recommended to do NEXT

2. 🟡 MEDIUM PRIORITY: youtube_manager.py
   - Would benefit from splitting
   - Not urgent
   - Can wait for next refactoring session

3. 🟢 LOW PRIORITY: All other files
   - database.py: Well-organized, keep as-is
   - statistics.py: Good structure, keep as-is
   - security.py: Single responsibility, keep as-is
   - Others: All acceptable sizes

================================================================================
IMPLEMENTATION PLAN FOR video_player.py SPLIT
================================================================================

Phase 1: Create playback/ directory structure
----------------------------------------------
1. Create pawvision/playback/ directory
2. Create __init__.py with exports
3. Create backends.py with player implementations
4. Create engine.py with PlaybackEngine class
5. Create video_utils.py with utility functions

Phase 2: Move code to new modules
----------------------------------
1. Extract duration/format utilities → video_utils.py
2. Extract player backends → backends.py
3. Extract process management → engine.py
4. Refactor video_player.py to use new modules

Phase 3: Update imports
-----------------------
1. Update main.py imports
2. Update web interface blueprint imports
3. Update any test files

Phase 4: Test
-------------
1. Test video playback
2. Test duration detection
3. Test player backend selection
4. Integration tests

Estimated Time: 2-3 hours
Risk Level: MEDIUM (core functionality)
Recommended: Do with thorough testing

================================================================================
SUMMARY
================================================================================

Files to Split:
  1. ✅ web_interface.py (DONE! 1,272 → 159 lines)
  2. ⚠️ video_player.py (RECOMMENDED: 631 → ~200 lines + 3 modules)
  3. 📋 youtube_manager.py (OPTIONAL: 492 → ~200 lines + 2 modules)

Files to Keep As-Is:
  ✅ database.py (561 lines) - Well-organized
  ✅ statistics.py (459 lines) - Single responsibility
  ✅ security.py (387 lines) - Good structure
  ✅ All files under 350 lines

Next Recommended Action:
  → Split video_player.py into playback/ module structure
  → This will give similar benefits to web_interface.py split
  → Will improve testability and maintainability significantly

Would you like me to:
  A) Proceed with splitting video_player.py?
  B) Create the playback/ structure first and review?
  C) Keep video_player.py as-is for now?
  D) Focus on something else?
"""
