# PawVision Improvement Plan

This document tracks the implementation work requested after the codebase review.

## Progress

1. **Complete** — Repair video-library and playback model contract drift. Added compatible entry methods, recognized valid YouTube playback sources, and removed references to nonexistent metadata fields.
2. **Complete** — Fix configuration and statistics initialization for relative paths by creating parent directories only when present.
3. **Complete** — Unify statistics event storage and dashboard queries. Video plays now use shared event constants, viewing duration is persisted, and React dashboard queries use the stored event schema.
4. **Complete** — Validate configuration updates atomically and complete configuration controls. API updates are allowlisted and validated before save; Reset and Test GPIO now call their APIs. Mutating API calls can be protected with `PAWVISION_API_TOKEN`, and the Flask secret is deployment-provided or generated.
5. **Complete** — Align frontend service contracts and improve playback/library feedback. YouTube uses explicit end-offset semantics; stale statistics and download endpoints were corrected; playback actions prevent duplicate requests and use the saved volume.
6. **Complete** — Align Docker deployment configuration and update affected documentation. Docker now uses `/data`, port `5001`, and explicit host/port settings; systemd installers preserve LAN access explicitly.
7. **Complete** — Added regression coverage for relative config paths and recorded viewing duration.
8. **Complete** — Migrated Python dependency management to uv with a committed lockfile, uv-based developer commands, CI, Docker, and installers.
9. **Complete** — Repaired the full test suite: database operations now report real outcomes, statistics retain compatibility fields, and fresh API blueprints are created for each Flask application instance.

## Implementation Notes

- Preserve the existing public API where practical while providing compatibility for stored data.
- Do not alter the user’s existing frontend lockfile changes.
- Record validation results here when implementation is complete.

## Validation

- `python3 -m compileall -q pawvision tests` — passed.
- `python3 -m unittest tests.test_config tests.test_statistics -v` — passed (15 tests).
- `cd frontend && npm run build:check` — passed.
- `uv lock --check` and `uv sync --locked --group dev` — passed during the uv migration.
- `uv run pytest -q` — passed (44 tests).
- `uv build` — passed (with existing setuptools license deprecation warnings).
