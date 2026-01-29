# Arc Overlay

<p align="center">
  <img src="arcoverlay.png" alt="Arc Overlay Logo" width="256" height="256">
</p>

**Arc Overlay** is a powerful, real-time overlay tool designed to enhance your gaming experience. By utilizing advanced OCR (Optical Character Recognition) and screen scanning technologies, it provides instant information about items, quests, and progression without requiring you to leave the game.

> [!IMPORTANT]
> This project is a modified version based on [Git: ArcCompanion](https://github.com/Joopz0r/ArcCompanion-public).
>
> Special thanks to [RaidTheory/arcraiders-data](https://github.com/RaidTheory/arcraiders-data) for providing the essential game data.


## ✨ Key Features

-   **🔍 Smart Item Overlay**: Instantly scan items on your screen to see their rarity, market value, and utility in quests or projects.
-   **📜 Quest Tracker**: Keep your active objectives in view with a customizable overlay. Never lose track of what you need to collect.
-   **📝 Patch Notes**: Check out the latest updates in [Patchnotes.md](Patchnotes.md).
-   **🏠 Hideout & Project Management**: Track your base progression and crafting requirements in a centralized "Progress Hub."
-   **🌍 Multi-Language OCR**: Supports 14+ languages (English, German, French, Spanish, Russian, Chinese, Japanese, and more).
-   **🎨 Premium Dark UI**: A sleek, modern interface built with PyQt6 that feels native to any gaming setup.
-   **⚡ High Performance**: Fast scanning powered by OpenCV and MSS for minimal impact on game performance.

## ⌨️ Default Hotkeys

Customizable in the settings:

-   **`Ctrl + F`**: Trigger Item Scan (OCR).
-   **`Ctrl + E`**: Toggle Quest Log Overlay.
-   **`Ctrl + H`**: Open the Progress Hub (Main Window).

## 🚀 Getting Started

### Prerequisites

-   Windows (10/11 recommended).
-   Tesseract-OCR (usually bundled with the installer).

### Installation

1.  Download the latest version from the [Releases](https://github.com/aalejandrofer/arcoverlay/releases) page.
2.  Install and run `ArcOverlay.exe`.
3.  The app will minimize to the system tray. Use the hotkeys or right-click the tray icon to access features.

### For Developers

If you want to run from source:

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Ensure Tesseract-OCR is installed and accessible.
4.  Run the application:
    ```bash
    python arcoverlay.py
    ```

## � Building (Windows 11)

To build the native Windows MSI installer, you must run the following command from a Windows terminal (not WSL):

```bash
python buildtools/msi_setup.py bdist_msi
```

The installer will be generated in the `dist/` directory.

## �🛠️ Built With

-   **[Python](https://www.python.org/)**: Core application logic.
-   **[PyQt6](https://riverbankcomputing.com/software/pyqt/)**: Modern GUI framework.
-   **[OpenCV](https://opencv.org/)**: Image processing for OCR preparation.
-   **[Tesseract-OCR](https://github.com/tesseract-ocr/tesseract)**: Optical Character Recognition engine.
-   **[MSS](https://github.com/bobun/python-mss)**: Ultra-fast screen capturing.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
