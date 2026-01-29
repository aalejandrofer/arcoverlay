# -*- mode: python ; coding: utf-8 -*-
# ArcOverlay PyInstaller Specification File

import os
import sys

# Calculate absolute paths
spec_dir = os.path.dirname(os.path.abspath(SPEC))
root_dir = os.path.dirname(spec_dir)

def get_path(path):
    return os.path.join(root_dir, path)

# Check for Tesseract presence during build
tess_exe = get_path(os.path.join("Tesseract-OCR", "tesseract.exe"))
if not os.path.exists(tess_exe):
    print(f"\nCRITICAL ERROR: 'tesseract.exe' is missing at: {tess_exe}")
    sys.exit(1)

block_cipher = None

# --- 1. HIDDEN IMPORTS ---
hidden_imports = [
    'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets',
    'pytesseract', 'Pillow', 'PIL', 'PIL.PngImagePlugin',
    'mss', 'cv2', 'numpy', 'pynput', 'pynput.keyboard', 'pynput.mouse',
    'pynput.keyboard._win32', 'pynput.mouse._win32', 'pyperclip', 'requests',
]

# Project Modules
hidden_imports.extend([
    'modules.app_updater', 'modules.base_page', 'modules.config_manager',
    'modules.constants', 'modules.data_manager', 'modules.hideout_manager_window',
    'modules.image_processor', 'modules.item_database_window', 'modules.overlay_ui',
    'modules.progress_hub_window', 'modules.project_manager_window',
    'modules.quest_manager_window', 'modules.scanner', 'modules.settings_window',
    'modules.ui_components', 'modules.update_checker',
])

# --- 2. DATA FILES ---
datas = [
    (get_path('arcoverlay.ico'), '.'),
    (get_path('arcoverlay.png'), '.'),
    (get_path('Tesseract-OCR'), 'Tesseract-OCR'), 
    (get_path('modules'), 'modules'),
    (get_path('data'), 'data'), # This includes the whole data folder
    (get_path('Images/build_icons'), 'data/images'), 
]

a = Analysis(
    [get_path('arcoverlay.py')],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'tkinter', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ArcOverlay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, 
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=get_path('arcoverlay.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ArcOverlay',
)