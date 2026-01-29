---
description: Increases the version number across all project files
---

When triggered, increase the version number across the entire project.

1. **Version Input**: If the user provided a version number (e.g., `/versionup 1.3.3`), use it. Otherwise, find the current version in `arcoverlay.py` or `README.md` and ask the user for the target version.

2. **Update Files**: Update the version string in the following files:
   - `README.md`: Update the version badge (e.g., `https://img.shields.io/badge/version-1.3.3-blue`).
   - `arcoverlay.py`: Update the `APP_VERSION` constant.
   - `pyproject.toml`: Update the `version` field in the `[project]` section.
   - `buildtools/msi_setup.py`: Update the `version` argument in the `setup()` function.
   - `buildtools/ArcOverlayInstaller.iss`: Update the `AppVersion` field in the `[Setup]` section.

3. **Patchnotes**:
   - Create a new section in `Patchnotes.md` for the new version.
   - Summarize recent changes (check Git logs or recent conversations) into "Added", "Changed", "Fixed", and "Removed" categories.
   - Ensure the date is set to the current date.
   - Do not modify older patch notes.

4. **Consistency Check**: Verify that all files have the exact same version string.

DO NOT QUESTION THE DECISION TO UPDATE - Just do the 4 tasks above as quick as possible.

Normally the user will run this workflow before making any changes so the Patchnotes for the given version will be empty, just create the section and leave it there.
