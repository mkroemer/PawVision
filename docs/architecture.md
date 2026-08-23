---
layout: pawvision-theme
title: Architecture & Raspberry Pi Roadmap
---
# Architecture & Raspberry Pi Roadmap

This page summarizes the current PawVision architecture and proposes small, practical improvements for Raspberry Pi deployments where reliability and simplicity matter most.

## Current Architecture (High Level)

PawVision is already organized in modular layers:

1. **Core services (`pawvision/`)**
   - `video_player.py`: playback orchestration
   - `video_library.py` + `database.py`: local/YouTube metadata persistence
   - `youtube_manager.py`: YouTube URL handling and download support
2. **API layer (`pawvision/api/`)**
   - focused Flask blueprints for playback, videos, YouTube, stream, config, and statistics
3. **Web interface (`frontend/`)**
   - React + TypeScript pages for control, library, config, and statistics
4. **Platform integration**
   - Raspberry Pi GPIO handling and install/deploy scripts

This structure is a strong base for a small self-hosted project.

## Target Use Case Alignment

Goal: a **small Raspberry Pi app** that can:

- play/stream **local files**
- play/stream **YouTube videos**
- **download videos** for stable playback
- provide a **simple but practical** web UI with modern styling

PawVision already supports these capabilities. The suggestions below focus on keeping the project lightweight and easy to maintain.

## Suggested Improvements (Minimal-Complexity First)

### 1) Add an explicit "Simple Mode" UI profile
- Keep the existing modern UI, but add a mode with only core controls:
  - Play / Pause
  - Next
  - Stop
  - Quick YouTube add/download
- Hide advanced settings unless expanded.

### 2) Local-first playback preference
- Keep YouTube download as first-class.
- Prefer downloaded/local files over temporary stream URLs to improve reliability on unstable Wi-Fi.

### 3) Lightweight library loading
- For larger collections on Pi hardware, paginate library entries and lazy-load thumbnails to reduce memory and startup cost.

### 4) Background housekeeping
- Add a low-frequency cleanup task for:
  - expired YouTube stream URLs
  - stale thumbnail cache files
  - optional max download storage threshold

### 5) Clear architecture guardrails
- Keep this separation stable:
  - `api/` = request/response and validation
  - service modules = business logic
  - frontend `services/` = API adapters
- This makes future changes safer and easier to test.

## Recommended Near-Term Plan

1. Ship UI **Simple Mode** first (highest user value, low risk).
2. Add **library pagination/lazy thumbnails** for Pi performance.
3. Add **storage & cache cleanup policy** for long-running installations.
4. Keep YouTube download UX prominent to reduce streaming failures.
