---
description: Major Code Review
---

🎯 Objective
Review the current state of the codebase following recent updates. Your priority is to ensure zero feature regression, maximum frame-rate stability for the user, and unshakeable code reliability.

🛠 Phase 1: Performance & Reliability Audit
Performance Budgeting: Analyze the OCR and Screen Capture loop. Any code path that adds >16ms of latency must be flagged or optimized to maintain 60FPS overlay responsiveness.

Dependency Audit: Check requirements.txt and imports. Remove any unused libraries and ensure all dependencies (PyQt6, OpenCV, MSS) are pinned to stable, high-performance versions.

Resource Management: Ensure that Tesseract processes and image handles are properly disposed of to prevent memory leaks during long gaming sessions.

⚙️ Phase 2: Refactoring & Feature Preservation
Feature Parity Check: Before refactoring, map out the "Smart Item Scan," "Quest Tracker," and "Progress Hub." Ensure that structural changes do not break the data flow between these components.

Robust Error Handling: Wrap all hardware-interacting code (Screen grab, OCR, Tray icons) in resilient try-except blocks that fail gracefully without crashing the entire overlay.

Type Safety: Enforce strict Python type hinting across all modules to ensure that "big updates" don't introduce silent type-conflict bugs.

📋 Phase 3: Documentation & Project Health
README Synchronization: Update README.md to reflect the current feature set, latest hotkeys, and any new installation steps.

Versioning: Update pyproject.toml or version constants to reflect the new build.

Future-Proofing: Suggest 3 specific "Next Step" features or architectural improvements based on your analysis of the current code's strengths and limitations.
