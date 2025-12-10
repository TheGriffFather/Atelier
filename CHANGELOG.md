# Changelog

All notable changes to Atelier will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Application Walkthrough** - Visual documentation with screenshots
  - New `docs/WALKTHROUGH.md` with annotated screenshots of all major sections
  - Covers Gallery, Timeline, Shows, Tracker, Outreach, Discovery, and Display Frame
  - Screenshots stored in `docs/Research Documentatiopn/Screen Caps/`

- **Display Settings Sync** - Cross-device settings synchronization via database
  - New `DisplaySettings` SQLAlchemy model for persistent storage
  - GET/PUT `/api/display/settings` REST endpoints
  - Settings now sync automatically between PC, tablet, and Raspberry Pi
  - Migration script for SQLite (`scripts/migrate_add_display_settings.py`)

- **Image Fit Modes** - Intelligent image scaling for the frame display
  - Auto mode: Detects optimal fit based on aspect ratio comparison
  - Contain mode: Fit entire image within frame (letterbox/pillarbox)
  - Cover mode: Fill frame completely (may crop edges)
  - Fill mode: Stretch to fill (may distort)
  - Auto-detection uses 15% threshold for aspect ratio comparison

- **Display Settings UI Enhancements**
  - Navigation arrows for browsing artwork in preview
  - Image Display mode selector with pill-button UI
  - Art Type filter chips with artwork counts
  - Improved frame preview styling

- **Frame Display Improvements**
  - Cursor auto-hide after 3 seconds (for kiosk/Pi displays)
  - Long-press (800ms) navigates to display settings
  - Settings loaded from API instead of localStorage

### Changed

- Frame display now fetches settings from database instead of URL query parameters
- Display settings page uses API persistence instead of localStorage
- Improved visual hierarchy in settings sections

## [0.1.0] - 2024-12-01

### Added

- Initial release of Atelier digital frame application
- FastAPI backend with SQLAlchemy async support
- Artwork management with full CRUD operations
- Touch-optimized frame display (`/frame`)
- Display settings page (`/display`)
- Frame style selection (wood, black, white, gold, none)
- Rotation interval configuration
- Title overlay toggle
- Verified-only artwork filtering
- Shuffle mode for random display order
- Artwork selection for curated displays
