import sys
import os
from cx_Freeze import setup, Executable

# Calculate absolute paths
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)

def get_path(path):
    return os.path.join(root_dir, path)


# Dependencies are automatically detected, but some might need help
build_exe_options = {
    "excludes": ["tkinter", "matplotlib", "scipy"],
    "include_files": [
        (get_path("arcoverlay.ico"), "arcoverlay.ico"),
        (get_path("arcoverlay.png"), "arcoverlay.png"),
        (get_path("Tesseract-OCR"), "Tesseract-OCR"),
        (get_path("modules"), "modules"),
        (get_path("data"), "data"),
    ],
    "packages": ["PyQt6", "pytesseract", "PIL", "mss", "cv2", "numpy", "pynput", "pyperclip", "requests"],
}

# MSI base options
bdist_msi_options = {
    "add_to_path": False,
    "initial_target_dir": f"[ProgramFilesFolder]\\ArcOverlay",
}

base = None
if sys.platform == "win32":
    base = "gui"

setup(
    name="ArcOverlay",
    version="1.3.3",
    description="ArcOverlay Client",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=[
        Executable(
            get_path("arcoverlay.py"),
            base=base,
            target_name="ArcOverlay.exe",
            icon=get_path("arcoverlay.ico"),
            shortcut_name="ArcOverlay",
            shortcut_dir="ProgramMenuFolder",
        )
    ],
)
