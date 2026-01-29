# Patch Notes

## [1.4.0] - 2026-01-29

### Added

- preparing for new major feature set.

### Removed

- **Update Logic & Repository Links**: Removed all scripts (`app_updater.py`, `update_checker.py`) and code related to application updates. The app is now independent of the old repository and update servers.
- **Updates Tab**: Removed the "Updates" tab from the settings window to reflect the removal of update services.

## [1.3.2] - 2026-01-29

### Added

- **Enhanced Live Preview**: The settings preview now displays dummy data for ALL categories (Trader Offers, Crafting, Hideout, Projects, Recycle/Salvage) for better layout visualization.
- **Rarity Visuals**: The overlay and preview now highlight the item's rarity with a colored top border.

### Changed

- **Unified Item Notes**: Replaced the "Custom Tags" system with a consolidated "User Notes" section across the Item Database and Overlay.
- **Improved Item Overlay UI**:
  - Removed bulky backdrops and borders from item images for a cleaner look.
  - Adjusted layout logic to prevent vertical stretching of the image section.
- **Settings Streamlining**: Removed the obsolete "Recommendation" logic and settings to focus on a more personalized experience.
- **Preview Stability**: Introduced a small initialization delay to ensure the live preview renders correctly on startup.

### Fixed

- **Layout Persistence**: Fixed an issue where the live preview layout wouldn't clear properly between updates.
- **Initial Rendering**: Solved the "blank preview" bug on first load by ensuring UI components are fully ready before drawing.

### Removed

- **Recommendations Section**: Completely removed automated recommendations in favor of User Notes.
- **Custom Tags UI**: Removed the redundant tag input from the Item Database inspector.
