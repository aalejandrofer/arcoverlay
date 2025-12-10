V1.3.0
**New Features & Major Improvements**
- **Backup System**: New Backup/Restore tab in settings to save and load your progress/config.
- **Hyperspeed OCR**: Optimized text recognition engine for significantly faster and more accurate tooltip reading.
- **Live Settings**: Adjusting hotkeys or overlay settings (like transparency) now updates instantly.
- **Anchor Mode**: Option to pin the Item Overlay to a fixed position (e.g., Top Left) instead of the mouse.
- **Opacity Slider**: Control the transparency of the Item Overlay background.

**Item Overlay Enhancements**
- Added drag-and-drop reordering for overlay sections
- Item overlay can now display storage quantities
- Added color picker for OCR color
- Roman Numeral OCR Fix (Il -> II, etc.)
- Smart Tooltip Cropping & Language Filtering for better performance

**Quest & Hideout Management**
- **Quest Overlay**: Added map names, search bar, and map filters.
- **Hideout Manager**: Remembers section states (open/closed) between sessions. Clearly shows when no upgrades are available.

**Item Database**
- Added quick filter buttons (Blueprints, Storage)
- Blueprint progress counter and collection tracking
- Dedicated inspector panel for item details
- Improved filtering (Tracked, Requirements) and multi-language search

**UI/UX Improvements**
- **Theming**: applied Dark Theme to all popups and dialogs.
- **Progress Hub**: Added Reset buttons that properly clear data and refresh the UI.
- **Window**: Prevented window from getting stuck off-screen or resetting position unexpectedly.
- **Settings**: Reorganized into a tabbed interface; "Reset" button now correctly restores defaults.
- Dynamic Monitor Detection (Auto-detects active monitor).

**Bug Fixes**
- Fixed application buttons becoming unresponsive after updates.
- Fixed overlay text size setting not applying.
- Fixed sync issues where overlay wouldn't reflect inventory changes immediately.
- Fixed Quest Hub items disappearing after refresh.
- Resolved various JSON parsing and config saving issues.
- Fixed "future hideout" and "projects" settings not affecting overlay.

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