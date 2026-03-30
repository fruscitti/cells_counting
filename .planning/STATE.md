# Project State

**Project:** Fluorescence Cell Counter — Desktop App + Batch Management
**Milestone:** v2.0
**Branch:** local-ui
**Last updated:** 2026-03-29 — Project initialized, planning complete

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-29)

**Core value:** Scientists can analyze fluorescence images offline, save named batches, and return to re-examine or modify sessions without a web browser.
**Current focus:** Phase 2 — Desktop GUI (not started)

## Current Position

Planning complete. Ready to begin execution.

Next step: `/gsd:plan-phase 2`

## Phase Status

| Phase | Name | Status |
|-------|------|--------|
| 2 | Desktop GUI | ○ Pending |
| 3 | Batch Management | ○ Pending |

## Key Decisions Made in Planning

- PySide6 (Qt for Python, LGPL) chosen over tkinter — better image widgets, native look on all platforms
- BGR→RGB conversion + QImage.copy() required when converting numpy arrays to QPixmap (prevents segfault)
- QRunnable + QThreadPool for background analysis — keeps UI responsive
- ScaledImageLabel (QLabel subclass) for image display — simpler than QGraphicsView for v1
- Folder structure + JSON manifest for batch storage — no database dependency
- Atomic save (write temp + os.replace) for manifest — prevents corruption on crash
- Remove-from-manifest-only (no file delete) on image removal — prevents research data loss
- All 9 parameters stored in manifest from day one (including tophat/adaptive params)
- Entry point: `app.py` — `main.py` (Gradio web version) stays untouched
