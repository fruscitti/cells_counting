# Feature Research

**Domain:** Scientific desktop app UI — menu bar, toolbar, keyboard shortcuts, status bar for a fluorescence microscopy cell counter
**Researched:** 2026-03-30
**Confidence:** HIGH (PySide6/Qt patterns are well-established; ImageJ/MIB conventions cross-validated)

---

## Context: What Exists Today

All actions live as stacked buttons in a fixed 278 px left panel. The current button inventory:

| Button | Current state |
|--------|---------------|
| Open Images | always enabled |
| Analyze | enabled when images loaded |
| Auto-Optimize | enabled when images loaded |
| Clear | always enabled |
| Save Batch | enabled when images loaded |
| Open Batch | always enabled |
| Add Images | enabled only when batch open |
| Remove Image | enabled when batch open + image selected |
| Re-Analyze | enabled when batch open + images loaded |
| Export CSV | enabled when batch open |
| Undo Mark | enabled when manual marks exist |
| Zoom controls (orig + ann) | inline per-panel buttons |
| Progress bar | visible during analysis |
| Status label | text in left panel |
| Cell count label | large bold label in left panel |

The UI redesign (v3.0) migrates these into: menu bar, toolbar, keyboard shortcuts, and a status bar — freeing the left panel for image list + parameter sliders only.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features scientists expect from any desktop app of this type. Missing these makes the app feel unfinished.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| File menu with Open and Exit | Universal desktop app convention (Qt, macOS, Windows HIG all require this) | LOW | Open Images maps to File > Open Images (Ctrl+O). Exit / Quit maps to File > Exit (Ctrl+Q on Windows/Linux, Cmd+Q on macOS — Qt handles this via `QKeySequence.Quit`) |
| Keyboard shortcut for Open | Power users expect Ctrl+O from day one | LOW | Defined once on the QAction, works from menu and shortcut simultaneously |
| Keyboard shortcut for Save | Ctrl+S is muscle memory for every desktop user | LOW | Maps to Save Batch. When batch is already open, saves in-place. First save prompts for name |
| Toolbar with primary action buttons | Scientists want one-click access to Analyze without hunting menus | LOW | Qt QToolBar with QActions shared with menu — no duplicate logic |
| Status bar at bottom of window | Standard QMainWindow pattern; shows app state at a glance | LOW | Qt provides `self.statusBar()` — already used in existing code (`statusBar().showMessage(...)`) |
| Status bar: current batch name | Users need to know which batch is open | LOW | Shows "No batch" when nothing open, batch name otherwise |
| Status bar: image count | How many images are loaded — basic orientation info | LOW | Updates on load/remove/clear |
| Status bar: total cell count | The primary output of the analysis — must be visible at all times | LOW | Sum of all images in results table; updates as analysis runs |
| Menu separators grouping related items | Without separators menus feel like an undifferentiated list | LOW | Qt `addSeparator()` — zero code cost |
| Ellipsis on items that open dialogs | Convention: "Save Batch..." signals a name prompt will appear | LOW | Naming convention only — no code complexity |
| Delete key to remove selected image | Power users expect keyboard-driven list management | LOW | QShortcut or keyPressEvent on the image list widget |
| Undo Mark accessible from menu | Destructive action needs menu discoverability | LOW | Analysis menu or Edit menu; Ctrl+Z is the expected shortcut |
| Window title reflects open batch | "Cell Counter — batch_name" is standard for document-oriented apps | LOW | Already implemented; menu bar migration must preserve this |

### Differentiators (Competitive Advantage)

Features that go beyond convention and match the scientific workflow.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Status bar: progress during analysis | Scientists want to know how many images remain without watching a separate dialog | LOW | Reuse existing `_on_progress` signal; write to a `QStatusBar` permanent widget or `showMessage` |
| Toolbar disabled-state management | Grayed-out toolbar buttons communicate "not available now" without cluttering the panel | LOW | QAction `setEnabled()` — identical logic to current button enable/disable, just moved to actions |
| Analysis menu grouping Analyze + Auto-Optimize + Re-Analyze | Groups all "run computation" commands together — mirrors ImageJ's Analyze menu convention | LOW | Logical grouping reduces cognitive load; no extra implementation |
| Batch menu as a first-class menu | "Batch" as a top-level menu (vs buried in File) signals that batch management is a primary workflow — unusual in generic apps, correct for scientists | LOW | File menu stays lean; Batch menu owns Save Batch, Open Batch, Add Images, Remove Image, Export CSV |
| Keyboard shortcut Ctrl+Shift+S for Save Batch | Ctrl+S is expected but if already-open batch saves silently, Ctrl+Shift+S for "Save As new batch" is a useful distinction | LOW | Standard secondary-save convention (matches Word, Photoshop) |
| Undo via Ctrl+Z | Ctrl+Z for Undo Mark matches every creative/scientific tool expectation; the app already has undo semantics, just needs the shortcut | LOW | Map QAction shortcut `QKeySequence.Undo` to existing `_on_undo_mark` |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Edit menu with Copy/Paste/Cut | Looks complete and professional | No text editing in this app — copy/paste doesn't apply to images or cell counts in this workflow. Adds a ghost menu that users will click and find empty | Skip entirely. If clipboard export of count is needed later, put it under File > Copy Results or Batch > Export CSV |
| Help > Keyboard Shortcuts dialog | Users ask "where are the shortcuts?" | Adds a dialog to write and maintain. Shortcuts shown inline in menus make this unnecessary | Qt automatically shows shortcut keys next to menu items — that IS the shortcuts reference |
| Toolbar text labels next to icons | Seems more legible | Makes toolbar very wide; scientific users are tool-savvy and learn icons quickly | Use tooltips (shown on hover) which Qt handles automatically from the QAction's text |
| Movable/floatable toolbar | Qt toolbars are movable by default | Scientists don't rearrange toolbars; movable toolbar can be accidentally torn off and lost. Confusing for non-technical users | Call `setMovable(False)` on the toolbar — keep it docked |
| Undo history stack (multiple levels) | "Undo everything back to baseline" sounds powerful | The current data model doesn't maintain a history of algo_centroids or removed_indices snapshots. Building a proper undo stack is a rewrite of the state model | Keep single-level undo (Undo Mark removes last manual mark). Document this scope clearly |
| Recent files submenu under File > Open Recent | Familiar pattern from document apps | Requires persisting a file recents list to disk (QSettings or a JSON file). Not high-value for a batch-oriented scientific tool | Open Batch dialog already lists all saved batches — that IS the recent-files equivalent |

---

## Feature Dependencies

```
QAction (unified action object)
    └──enables──> Menu item (QMenu)
    └──enables──> Toolbar button (QToolBar)
    └──enables──> Keyboard shortcut (QKeySequence)
    (all three stay in sync via single setEnabled() call)

Status bar (QStatusBar)
    └──requires──> Analysis signals already emitted by AnalysisWorker
    └──requires──> Batch state (_current_batch_dir, _images) already tracked

Keyboard shortcut Delete (remove image)
    └──requires──> Image selected in image_list (existing state)
    └──maps-to──> existing _on_remove_image()

Ctrl+Z (Undo Mark)
    └──maps-to──> existing _on_undo_mark()
    └──requires──> undo_mark action setEnabled() tied to marks existing (already done for button)

Batch menu actions
    └──maps-to──> existing _on_save_batch, _on_open_batch, _on_add_images,
                  _on_remove_image, _on_re_analyze, _on_export_csv
    └──enable/disable logic──> _update_batch_buttons() (already exists, reuse)
```

### Dependency Notes

- **QAction is the central pattern:** In Qt, a single QAction object can be added to a menu AND a toolbar simultaneously. Shortcut, enabled state, and text are defined once. This is how the migration works: replace each button signal with a QAction, add it to both the relevant menu and the toolbar where appropriate.
- **Status bar already partially wired:** The existing code calls `self.statusBar().showMessage(...)` in several places. The full status bar feature just formalizes this into permanent widgets (batch name, image count, cell count) plus the existing transient messages.
- **`_update_batch_buttons()` must become `_update_actions()`:** The existing method enables/disables individual button widgets. After migration it needs to enable/disable QAction objects. The logic (which conditions enable which action) is identical — only the target objects change.

---

## MVP Definition (for this milestone)

This is a UI restructuring milestone — the features listed below are the entire scope. There is no "defer to v2" here because these items are all in PROJECT.md as active requirements.

### Launch With (v3.0)

- [ ] Menu bar with three menus: File, Batch, Analysis — all current left-panel buttons moved in
- [ ] Toolbar with four actions: Analyze, Auto-Optimize, Undo Mark, Clear
- [ ] Keyboard shortcuts: Ctrl+O (Open Images), Ctrl+S (Save Batch), Ctrl+Shift+S (Save Batch As), Ctrl+Z (Undo Mark), Delete (Remove Image from list), Ctrl+Q (Quit)
- [ ] Status bar: permanent widgets for batch name, image count, cell count; transient messages for progress/completion
- [ ] Left panel freed of all action buttons — contains only image list + parameter sliders
- [ ] `_update_batch_buttons()` refactored to `_update_actions()` targeting QActions

### Explicitly Out of Scope for This Milestone

- Edit menu — no applicable semantics
- Help menu / shortcuts dialog — Qt shows shortcuts inline in menus
- Movable toolbar — disable with `setMovable(False)`
- Undo history beyond single-step — existing model doesn't support it
- Recent files list — Open Batch dialog covers this

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| QAction-based menu bar (File/Batch/Analysis) | HIGH | LOW | P1 |
| Toolbar (Analyze, Auto-Optimize, Undo Mark, Clear) | HIGH | LOW | P1 |
| Status bar with batch name + image count + cell count | HIGH | LOW | P1 |
| Keyboard shortcuts (Ctrl+O, Ctrl+S, Ctrl+Z, Delete) | HIGH | LOW | P1 |
| `_update_actions()` replacing `_update_batch_buttons()` | HIGH | LOW | P1 — correctness depends on this |
| Progress feedback in status bar during analysis | MEDIUM | LOW | P1 — status bar already partially wired |
| Toolbar `setMovable(False)` | MEDIUM | LOW | P1 — prevents accidental detach |
| Ctrl+Q / Cmd+Q quit shortcut | MEDIUM | LOW | P1 — platform expectation |
| Ctrl+Shift+S Save As new batch | LOW | LOW | P2 — nice but Ctrl+S covers most cases |

---

## Mapping: Current Buttons to New Locations

| Current Button | Menu | Toolbar | Keyboard Shortcut |
|---------------|------|---------|-------------------|
| Open Images | File > Open Images... | — | Ctrl+O |
| Clear | File > Clear | Yes | — |
| Save Batch | Batch > Save Batch | — | Ctrl+S |
| Open Batch... | Batch > Open Batch... | — | Ctrl+Shift+O |
| Add Images... | Batch > Add Images... | — | — |
| Remove Image | Batch > Remove Image | — | Delete |
| Re-Analyze | Batch > Re-Analyze | — | — |
| Export CSV... | Batch > Export CSV... | — | — |
| Analyze | Analysis > Analyze | Yes | Ctrl+Return |
| Auto-Optimize | Analysis > Auto-Optimize | Yes | — |
| Re-Analyze | Analysis > Re-Analyze (duplicate) | — | — |
| Undo Mark | Analysis > Undo Mark | Yes | Ctrl+Z |
| — (quit) | File > Exit | — | Ctrl+Q (Win/Linux), Cmd+Q (macOS) |

Note: Re-Analyze fits in both Batch and Analysis menus logically. Best placement is **Batch > Re-Analyze** because it operates on the batch (requires an open batch) — consistent with enable/disable logic.

---

## Competitor Feature Analysis

| Feature | ImageJ/Fiji | Microscopy Image Browser (MIB) | This App's Approach |
|---------|-------------|-------------------------------|---------------------|
| Primary analysis entry point | Analyze menu (top-level) | Toolbar + panel buttons | Analysis menu + toolbar (Analyze button) |
| File operations | File > Open, Import | File menu | File menu: Open Images, Clear, Exit |
| Batch operations | Process > Batch | Batch processing panel | Batch menu (first-class menu) |
| Keyboard shortcut for analyze | Varies by plugin | App-defined | Ctrl+Return (unambiguous in scientific context) |
| Status bar content | Image info, cursor position | Image dimensions, memory usage | Batch name + image count + total cell count |
| Undo | Edit > Undo (Ctrl+Z) | Ctrl+Z | Ctrl+Z (single level, mapped to Undo Mark) |
| Toolbar movability | Docked, not movable | Docked | Docked, `setMovable(False)` |

---

## Sources

- [Python and PyQt: Creating Menus, Toolbars, and Status Bars — Real Python](https://realpython.com/python-menus-toolbars/) — HIGH confidence: official tutorial, current
- [PySide6 Toolbars, Menus & QAction — pythonguis.com](https://www.pythonguis.com/tutorials/pyside6-actions-toolbars-menus/) — HIGH confidence: PySide6-specific, widely referenced
- [QMenuBar Class — Qt 6 Docs](https://doc.qt.io/qt-6/qmenubar.html) — HIGH confidence: official Qt documentation
- [Application Main Window — Qt for Python](https://doc.qt.io/qtforpython-6.8/overviews/qtwidgets-mainwindow.html) — HIGH confidence: official Qt for Python docs
- [ImageJ Analyze Menu](https://imagej.net/ij/docs/menus/analyze.html) — MEDIUM confidence: domain reference for scientific app conventions
- [Microscopy Image Browser features](https://mib.helsinki.fi/features_all.html) — MEDIUM confidence: peer scientific desktop app for reference patterns
- Existing `ui/main_window.py` — HIGH confidence: ground truth for what currently exists

---
*Feature research for: UI restructuring — menu bar, toolbar, keyboard shortcuts, status bar in fluorescence microscopy cell counter desktop app*
*Researched: 2026-03-30*
