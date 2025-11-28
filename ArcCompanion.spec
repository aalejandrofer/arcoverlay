# -*- mode: python ; coding: utf-8 -*-
# ArcCompanion PyInstaller Specification File

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all hidden imports
hidden_imports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'pytesseract',
    'Pillow',
    'PIL',
    'pynput',
    'pynput.keyboard',
    'pynput.mouse',
    'rapidfuzz',
    'pyperclip',
    'pystray',
    'scipy',
    'numpy',
]

# Collect all modules from the modules directory
hidden_imports.extend([
    'modules.base_manager_window',
    'modules.constants',
    'modules.data_manager',
    'modules.hideout_manager_window',
    'modules.image_processor',
    'modules.item_database_window',
    'modules.overlay_ui',
    'modules.progress_hub_window',
    'modules.project_manager_window',
    'modules.quest_manager_window',
    'modules.settings_window',
    'modules.ui_components',
    'modules.update_checker',
])

# Define data files to include
datas = [
    ('arccompanion.ico', '.'),  # Include icon in root
    ('arccompanion.png', '.'),  # Include PNG logo
    ('Tesseract-OCR', 'Tesseract-OCR'),  # Include entire Tesseract-OCR folder
    ('modules', 'modules'),  # Include modules as package

    # --- BUNDLED ASSETS (Inside EXE) ---
    # These specific files get frozen inside the executable
    ('data/images/coins.svg',        'bundled_assets'),
    ('data/images/coins.png',        'bundled_assets'),
    ('data/images/support_banner.png', 'bundled_assets'),
]

# NOTE: The rest of 'data' (items/quests/hideout) is intentionally excluded 
# so it can be updated separately by the user/update checker.

a = Analysis(
    ['arc_companion.py'],
    pathex=[],
    binaries=[],
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='arccompanion.ico',
)