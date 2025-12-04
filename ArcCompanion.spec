# -*- mode: python ; coding: utf-8 -*-
# ArcCompanion PyInstaller Specification File

import os
import sys

# Check for Tesseract presence during build
tess_exe = os.path.join("Tesseract-OCR", "tesseract.exe")
if not os.path.exists(tess_exe):
    print(f"\nCRITICAL ERROR: 'tesseract.exe' is missing!")
    sys.exit(1)

block_cipher = None

# --- 1. HIDDEN IMPORTS ---
hidden_imports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'pytesseract',
    'Pillow',
    'PIL',
    'mss',           # <--- MSS for Screen Capture
    'cv2',           # <--- OpenCV for Image Processing
    'numpy',
    'pynput',
    'pynput.keyboard._win32',
    'pynput.mouse._win32',
    'pyperclip',
    'requests',
]

# Project Modules
hidden_imports.extend([
    'modules.app_updater',
    'modules.base_page', 
    'modules.config_manager',
    'modules.constants',
    'modules.data_manager',
    'modules.hideout_manager_window',
    'modules.image_processor',
    'modules.item_database_window',
    'modules.overlay_ui',
    'modules.progress_hub_window',
    'modules.project_manager_window',
    'modules.quest_manager_window',
    'modules.scanner',
    'modules.settings_window',
    'modules.ui_components',
    'modules.update_checker',
])

# --- 2. DATA FILES ---
datas = [
    ('arccompanion.ico', '.'),
    ('arccompanion.png', '.'),
    ('Tesseract-OCR', 'Tesseract-OCR'), 
    ('modules', 'modules'),

    # Bundled Assets
    ('data/images/coins.svg',        'bundled_assets'),
    ('data/images/coins.png',        'bundled_assets'),
    ('data/images/support_banner.png', 'bundled_assets'),
]

a = Analysis(
    ['arc_companion.py'],
    pathex=[],
    binaries=[],  # <--- Scipy binaries removed
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'tkinter', 'scipy'], # <--- Explicitly exclude scipy
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ArcCompanion',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, 
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='arccompanion.ico',
)