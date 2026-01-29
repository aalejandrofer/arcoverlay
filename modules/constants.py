import os
import sys

def get_base_path():
    """
    Determines the base path for resources (icons/images bundled inside the EXE).
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return sys._MEIPASS
    except AttributeError:
        return os.path.abspath(".")

def get_writable_data_dir():
    """
    Determines where to save User Data (JSONs, downloaded images).
    Robust cross-platform implementation.
    """
    # Detect if we are on a problematic filesystem (WSL share from Windows)
    is_wsl_share = sys.platform == 'win32' and (
        os.path.abspath(".").startswith("\\\\wsl") or 
        os.path.abspath(".").startswith("\\\\wsl.localhost")
    )

    if getattr(sys, 'frozen', False) or is_wsl_share:
        if sys.platform == 'win32':
            # Use LocalAppData on Windows to ensure native filesystem (no network locking issues)
            base = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser("~")), 'ArcOverlay', 'data')
            if is_wsl_share and not getattr(sys, 'frozen', False):
                print(f"[INFO] WSL Share detected. Redirecting data to native Windows path: {base}")
        else:
            # Linux/macOS standard: ~/.local/share/ArcOverlay
            base = os.path.join(os.path.expanduser("~"), ".local", "share", "ArcOverlay", "data")
    else:
        # Standard development mode on native filesystem: use local data folder
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    
    try:
        os.makedirs(base, exist_ok=True)
    except Exception:
        # Absolute fallback to home directory if project dir is not writable
        base = os.path.join(os.path.expanduser("~"), ".arcoverlay_data")
        os.makedirs(base, exist_ok=True)
        
    return base

class Constants:
    # --- DYNAMIC DATA PATH ---
    DATA_DIR = get_writable_data_dir()
    
    ITEMS_DIR = os.path.join(DATA_DIR, 'items')
    HIDEOUT_DIR = os.path.join(DATA_DIR, 'hideout')
    QUESTS_DIR = os.path.join(DATA_DIR, 'quests')
    MAPS_DIR = os.path.join(DATA_DIR, 'maps') 
    
    # --- TESSERACT LANGUAGES ---
    TESSDATA_DIR = os.path.join(DATA_DIR, 'tessdata')
    
    LANGUAGES = {
        "English": ("en", "eng"),
        "German": ("de", "deu"),
        "French": ("fr", "fra"),
        "Spanish": ("es", "spa"),
        "Portuguese": ("pt", "por"),
        "Polish": ("pl", "pol"),
        "Russian": ("ru", "rus"),
        "Italian": ("it", "ita"),
        "Japanese": ("ja", "jpn"),
        "Chinese (Simplified)": ("zh-CN", "chi_sim"),
        "Chinese (Traditional)": ("zh-TW", "chi_tra"),
        "Korean": ("kr", "kor"),
        "Turkish": ("tr", "tur"),
        "Ukrainian": ("uk", "ukr")
    }

    # --- File Paths (External) ---
    CONFIG_FILE = os.path.join(DATA_DIR, 'config.ini')
    PROGRESS_FILE = os.path.join(DATA_DIR, 'progress.json')
    PROGRESS_DB = os.path.join(DATA_DIR, 'progress.db')
    TRADES_FILE = os.path.join(DATA_DIR, 'trades.json') 
    PROJECTS_FILE = os.path.join(DATA_DIR, 'projects.json') 
    MAPS_FILE = os.path.join(DATA_DIR, 'maps.json')

    # --- INTERNAL RESOURCES ---
    ICON_FILE = os.path.join(get_base_path(), 'arcoverlay.ico')
    
    if getattr(sys, 'frozen', False):
        _ASSETS_DIR = os.path.join(sys._MEIPASS, 'data', 'images')
    else:
        # Core UI icons moved here to be tracked by git
        _ASSETS_DIR = os.path.join(os.path.abspath("."), "Images", "build_icons")
    
    # Currency Icons
    _COIN_SVG = os.path.join(_ASSETS_DIR, 'coins.svg')
    _COIN_PNG = os.path.join(_ASSETS_DIR, 'coins.png')
    COIN_ICON_PATH = _COIN_SVG if os.path.exists(_COIN_SVG) else (_COIN_PNG if os.path.exists(_COIN_PNG) else None)
    
    # Storage Icons (New)
    _STORAGE_SVG = os.path.join(_ASSETS_DIR, 'storage.svg')
    _STORAGE_PNG = os.path.join(_ASSETS_DIR, 'storage.png')
    STORAGE_ICON_PATH = _STORAGE_SVG if os.path.exists(_STORAGE_SVG) else (_STORAGE_PNG if os.path.exists(_STORAGE_PNG) else None)

    # Redesign Icons
    QUEST_ICON_PATH = os.path.join(_ASSETS_DIR, 'quest_icon.png')
    HIDEOUT_ICON_PATH = os.path.join(_ASSETS_DIR, 'hideout_icon.png')
    PROJECT_ICON_PATH = os.path.join(_ASSETS_DIR, 'project_icon.png')
    RECYCLE_ICON_PATH = os.path.join(_ASSETS_DIR, 'recycle_icon.png')
    SALVAGE_ICON_PATH = os.path.join(_ASSETS_DIR, 'recycle_icon.png') # Using recycle icon as fallback/shared for now
    
    # Validation helper to avoid UI crashes
    @classmethod
    def get_icon(cls, path):
        return path if path and os.path.exists(path) else None
    

    # PyQt Stylesheet
    DARK_THEME_QSS = """
    QWidget {
        font-family: "Segoe UI", "Inter", sans-serif;
        font-size: 14px;
        color: #E0E6ED;
    }
    
    ProgressHubWindow, ItemDatabaseWindow, SettingsWindow {
        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                                          stop:0 #1E222A, stop:1 #121418);
    }

    HideoutManagerWindow, QuestManagerWindow, ProjectManagerWindow, BaseManagerWindow {
        background-color: transparent;
    }
    
    QWidget#scroll_content {
        background-color: transparent;
    }

    QFrame#StationFrame, QFrame#QuestFrame, QFrame#ProjectFrame, QFrame#card {
        background-color: rgba(26, 31, 43, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        margin-top: 8px;
    }

    QFrame#StationFrame { border-top: 2px solid #4476ED; }
    QFrame#QuestFrame   { border-top: 2px solid #98C379; }
    QFrame#ProjectFrame { border-top: 2px solid #ED9A44; }

    QLabel[objectName="Header"] {
        font-size: 18px;
        font-weight: bold;
        color: #FFF;
        border: none;
        padding-bottom: 5px;
    }

    QLineEdit {
        background-color: rgba(35, 40, 52, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 8px;
        border-radius: 6px;
        color: white;
    }
    QLineEdit:focus {
        border: 1px solid #4476ED;
        background-color: rgba(35, 40, 52, 1.0);
    }
    
    QComboBox {
        background-color: rgba(35, 40, 52, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
        padding: 6px 12px;
        color: #E0E6ED;
        min-width: 120px;
    }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background-color: #1A1F2B;
        selection-background-color: #4476ED;
        color: #E0E6ED;
        border: 1px solid #333;
        border-radius: 4px;
    }

    QPushButton {
        background-color: #2D333B;
        color: #E0E6ED;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: 600;
    }
    QPushButton:hover {
        background-color: #3E4451;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    QPushButton:pressed {
        background-color: #232834;
    }
    QPushButton:disabled {
        background-color: #1A1F26;
        color: #5C6370;
    }
    
    QPushButton[objectName="inv_button"] {
        background-color: rgba(35, 40, 52, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 5px;
        font-weight: bold;
        border-radius: 4px;
    }
    QPushButton[objectName="inv_button"]:hover {
        background-color: #4476ED;
        color: white;
    }

    QScrollArea {
        border: none;
        background-color: transparent;
    }
    
    QScrollBar:vertical {
        border: none;
        background: transparent;
        width: 8px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: rgba(255, 255, 255, 0.1);
        min-height: 30px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgba(255, 255, 255, 0.2);
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QTabWidget::pane {
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        background-color: rgba(26, 31, 43, 0.3);
        top: -1px;
    }
    QTabBar::tab {
        background-color: transparent;
        color: #9DA5B4;
        padding: 12px 24px;
        border-bottom: 2px solid transparent;
        margin-right: 4px;
        font-weight: 600;
    }
    QTabBar::tab:hover {
        color: white;
        background-color: rgba(255, 255, 255, 0.03);
    }
    QTabBar::tab:selected {
        color: #4476ED;
        border-bottom: 2px solid #4476ED;
        background-color: rgba(68, 118, 237, 0.05);
    }

    QToolTip {
        background-color: #121418;
        color: #E0E6ED;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        padding: 8px;
    }

    QCheckBox {
        spacing: 8px;
        color: #E0E6ED;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        background-color: rgba(35, 40, 52, 0.8);
    }
    QCheckBox::indicator:hover {
        border: 1px solid #4476ED;
    }
    QCheckBox::indicator:checked {
        background-color: #4476ED;
        border: 1px solid #4476ED;
        image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjMiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiPjwvcG9seWxpbmU+PC9zdmc+);
    }

    QProgressBar {
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 6px;
        background-color: rgba(35, 40, 52, 0.4);
        text-align: center;
        height: 12px;
    }
    QProgressBar::chunk {
        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #4476ED, stop:1 #61AFEF);
        border-radius: 5px; 
    }

    QMessageBox, QProgressDialog {
        background-color: #1E222A;
        color: #E0E6ED;
    }
    QMessageBox QPushButton {
        min-width: 80px;
    }

    QMenu {
        background-color: #1E222A;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
        padding: 4px;
    }
    QMenu::item {
        padding: 6px 24px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #4476ED;
        color: white;
    }
    QMenu::separator {
        height: 1px;
        background: rgba(255, 255, 255, 0.05);
        margin: 4px 8px;
    }
    """

    RARITY_COLORS = {
        "Common": "#ABB2BF",
        "Uncommon": "#98C379",  # Kept natural green
        "Rare": "#4476ED",      # Deeper, premium blue
        "Epic": "#BB86FC",      # Modern soft purple
        "Legendary": "#FFD700"  # Bright gold
    }
    QUEST_HEADER_COLOR = "#E5C07B" 
    QUEST_OBJECTIVE_COLOR = "#E0E6ED"