V1.3.0
**Item Overlay Enhancements**
- Added drag-and-drop reordering for overlay sections in settings
- Overlay sections now display in custom user-defined order
- Settings checkboxes now display green ticks when enabled
- Improved live preview of overlay appearance in settings
- Item overlay can now display how much you have in storage
- Added toggle for ultra-wide monitors
- Added color picker for OCR color

**Quest Overlay Enhancements**
- Added Map names for quests
- Added search bar for quests
- Added map filters for quests

**Item Database**
- Added quick filter buttons for Blueprints and Storage
- Blueprint progress now shown as "Collected/Total" counter
- Enhanced blueprint collection tracking with visual indicators
- Added storage tracking with visual indicators
- Added dedicated inspector panel for item details
- Improved item search with multi-language support
- Added filtering by: Tracked, Storage, Quest Requirements, Hideout Requirements, Project Requirements
- Added item requirement details showing which quests/hideout/projects need each item

**Language & Localization**
- Fixed overlay text to display in selected language for all item information
- Improved language file handling and download process
- Enhanced multi-language search capabilities

**OCR & Performance**
- Optimized tooltip OCR for faster and more reliable captures
- Pre-loading Tesseract worker for improved performance
- Cropped tooltip processing to header section only
- Fixed screenshot path handling on Windows
- added support for widescreen monitors
- added more debug options and settings for OCR

**UI/UX Improvements**
- Reorganized settings into tabbed interface (General, Item Overlay, Quest Overlay)
- Improved visual styling for better contrast and readability
- Added separator lines between overlay sections
- Enhanced item cards with rarity-based color coding
- Added toggle for top banner in progress hub
- Added Phase 5 to expeditions

**Bug Fixes**
- Fixed "future hideout" and "projects" settings not affecting overlay display
- Fixed QThread and QLabel runtime errors
- Fixed color match settings handling
- Resolved JSON parsing errors in item data files
- Fixed quest movement display updates
- Fixed config defaults not saving on first run

V1.2.1
Added 'Check for Updates' button in About tab.
Fixed Quest Overlay closing immediately when mouse no close.


V1.2.0
Mouse distance from overlay will dismiss overlay
Requesting another item check dismisses previous displayed overlay
Moved settings to the progress hub tab
Moved some settings around
added discord link banner

V1.1.0
Fixed issue with future requirements setting not working and always showing future requirements.
Added support for other languages.
Fixed issue with item database not showing all items.

V1.0.0
Initial release