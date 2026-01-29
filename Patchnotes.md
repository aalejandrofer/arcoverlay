# Patch Notes

## [1.3.4] - 2026-01-29

### Fixed

- **Migration Bug**: Fixed undefined variable bug in `data_manager.py` that could crash during JSON to SQLite migration when tracked items were stored in dict format.
- **Platform Safety**: Added Windows platform check in screen capture module to prevent crashes on macOS/Linux with a clear error message.

### Changed

- **Dependency Cleanup**: Removed unused `pystray` package from dependencies (PyQt6's `QSystemTrayIcon` is used instead).
- **Performance**: Added caching for language-filtered items in the scanner to avoid rebuilding the list on every scan.
- **OCR Caching**: Added LRU cache for OCR results to skip expensive Tesseract calls when hovering the same item repeatedly.

## [1.3.3] - 2026-01-29

### Added

- **Enhanced Live Preview**: The settings preview now displays dummy data for ALL categories (Trader Offers, Crafting, Hideout, Projects, Recycle/Salvage) for better layout visualization.
- **Quest Overlay Preview**: Added a high-fidelity live preview to the Quest Overlay settings tab, matching the main overlay's glassmorphism style.
- **Unified Settings**: Consolidated "Data Management" and "Updates" tabs into a single "Updates" tab.
- **Improved Settings UI**: Fixed truncated tab names, removed distracting tab backgrounds, and moved the "About" section into the Settings window.
- **Automated Data Updates**: The app now checks for game data updates on startup (comparing with GitHub commit time) and prompts the user to sync.
- **Data Timestamp**: added a "Last Updated" timestamp in the settings to track when the game data was last synced.
- **Database Update Integration**: Added a new "Update Database" feature in the Settings menu to fetch the latest game data and items.
- **Progress Tracking**: Integrated progress bars and status indicators for the database update process.
- **Completion Settings**: Added "Show Completed Hideout" and "Show Completed Project" toggles in settings to filter finished requirements.

### Changed

- **UI Streamlining**: Removed the obsolete "Recommendation" and "Custom Tags" systems to focus on a more personalized experience and cleaner interface.
- **Consolidated Item Notes**: Full removal of tags from the database and UI, leaving only the "User Notes" section.
- **Header Styling**: Removed backdrop and border from the item image in the overlay header for a minimalistic look.
- **Price Display**: Moved price next to Stash info, removed coin icon, and applied yellow accent color for cleaner visibility.
- **Requirement Styling**: Changed bullet points from `[ ]` to `-` and added strikethrough for completed requirements.
- **Trader Info**: Updated trader display format to show precise cost and limit details (e.g., "Trader: CostItem xQty (Limit)").

### Fixed

- Fixed Projects Tab empty state bug where projects were not being displayed.
- Fixed Settings UI crash related to QProgressBar name error.
- Fixed Settings visibility preview not updating when toggling section visibility.
- Fixed Overlay header layout expansion when sections are hidden.
- Fixed Overlay window sizing issues where it would cover the full screen or not shrink to fit content.
- Fixed Settings Preview box rendering where it would stretch to the bottom of the window unnecessarily.
- Fixed uneven vertical margins in the User Notes section.
- Fixed truncated tab names in the Settings Window by adjusting minimum tab width.
- Fixed truncated "Default" button in Scanning settings by increasing its width.
- **UI Initialization**: Improved the reliability of the settings window initialization.

## [1.3.2] - 2026-01-29 (Internal)

### Added

- **Rarity Visuals**: The overlay and preview now highlight the item's rarity with a colored top border.

### Changed

- **Improved Item Overlay UI**:
  - Removed bulky backdrops and borders from item images for a cleaner look.
  - Adjusted layout logic to prevent vertical stretching of the image section.
- **Preview Stability**: Introduced a small initialization delay to ensure the live preview renders correctly on startup.

### Fixed

- **Layout Persistence**: Fixed an issue where the live preview layout wouldn't clear properly between updates.
- **Initial Rendering**: Solved the "blank preview" bug on first load by ensuring UI components are fully ready before drawing.
