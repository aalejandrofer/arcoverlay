# -*- mode: python ; coding: utf-8 -*-
# ArcCompanion PyInstaller Specification File

import os

tess_exe = os.path.join("Tesseract-OCR", "tesseract.exe")
if not os.path.exists(tess_exe):
    print(f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"CRITICAL ERROR: 'tesseract.exe' is missing!")
    print(f"Location looked for: {os.path.abspath(tess_exe)}")
    print(f"Your Tesseract-OCR folder is likely empty or missing binaries.")
    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
    sys.exit(1) # Stop the build immediately
# --------------------
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# --- 1. COLLECT BINARIES FOR MATH LIBRARIES ---
# This is the vital part missing from your spec. 
# Without this, the EXE has the code but not the engines to run Scipy/Rapidfuzz.
scipy_bin, scipy_data, scipy_hidden = collect_all('scipy')
rf_bin, rf_data, rf_hidden = collect_all('rapidfuzz')

# --- 2. HIDDEN IMPORTS ---
hidden_imports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'pytesseract',
    'Pillow',
    'PIL',
    'pynput',
    'pynput.keyboard._win32', # Critical for Hotkeys
    'pynput.mouse._win32',
    'pyperclip',
    'numpy',
    'requests', 
    # Critical Scipy/Image components
    'scipy',
    'scipy.ndimage',
    'scipy.special',
    'scipy.spatial.transform',
]

# Add the extra imports found by collect_all
hidden_imports.extend(scipy_hidden)
hidden_imports.extend(rf_hidden)

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

# --- 3. DATA FILES ---
datas = [
    ('arccompanion.ico', '.'),
    ('arccompanion.png', '.'),
    ('Tesseract-OCR', 'Tesseract-OCR'), 
    ('modules', 'modules'),  # Keeping your preference to include this as data

    # Bundled Assets
    ('data/images/coins.svg',        'bundled_assets'),
    ('data/images/coins.png',        'bundled_assets'),
    ('data/images/support_banner.png', 'bundled_assets'),
]

# Add the extra data files found by collect_all
datas.extend(scipy_data)
datas.extend(rf_data)

# --- 4. BINARIES ---
# This was empty in your file, which is why Scipy failed.
binaries = []
binaries.extend(scipy_bin)
binaries.extend(rf_bin)

a = Analysis(
    ['arc_companion.py'],
    pathex=[],
    binaries=binaries, # Pass the collected binaries here
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'tkinter'], 
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
    console=False, # TEMPORARILY set to True to see errors if it still fails
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='arccompanion.ico',
)