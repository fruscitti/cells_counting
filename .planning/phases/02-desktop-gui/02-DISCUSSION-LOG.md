# Phase 2: Desktop GUI - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in CONTEXT.md — this log preserves the discussion.

**Date:** 2026-03-29
**Phase:** 02-desktop-gui
**Mode:** discuss
**Areas discussed:** App visual style, Analysis progress UX, Error display, Parameter panel layout

## Gray Areas Presented

| Area | Options presented |
|------|-------------------|
| App visual style | System-native · Dark mode · Fusion style |
| Analysis progress UX | Status label + progress bar · Per-image live table · Both |
| Error display | Warning row in table · Status bar message · Skip silently |
| Parameter panel layout | Single vertical list · Basic/Advanced collapsible · Tabs |

## Decisions Made

### App Visual Style
- **Chosen:** System-native Qt look
- **Rejected:** Dark mode, Fusion style

### Analysis Progress UX
- **Chosen:** Status label + progress bar (single bar for batch + current file label)
- **Rejected:** Per-image live table updates, Both

### Error Display
- **Chosen:** Warning row in results table (count=0, ⚠ Error indicator)
- **Rejected:** Status bar message, Skip silently

### Parameter Panel Layout
- **Chosen:** Single vertical list, all controls always visible (top-hat sub-controls toggled by checkbox)
- **Rejected:** Basic/Advanced collapsible sections, Tabs

## Corrections Made

No corrections — all recommended options were confirmed.

## Prior Decisions Applied (from STATE.md)

- PySide6 chosen over tkinter
- QRunnable + QThreadPool for background analysis
- ScaledImageLabel (QLabel subclass) for image display
- BGR→RGB conversion + QImage.copy() required
- Entry point: app.py (main.py stays untouched)
