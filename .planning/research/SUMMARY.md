# Project Research Summary

**Project:** Cell Counter — PySide6 Desktop App UI v3.0 Redesign
**Domain:** Scientific desktop application UI migration (PySide6 QMainWindow)
**Researched:** 2026-03-30
**Confidence:** HIGH

## Executive Summary

This milestone is a pure UI restructuring of an existing, functioning PySide6 desktop application. The goal is to migrate ~15 action buttons from a fixed-width left panel into a proper `QMenuBar` + `QToolBar` + `QStatusBar` combination, replace the fixed-width sidebar with a user-resizable `QSplitter`, and add keyboard shortcuts — without touching any business logic, workers, or data model. Every target API (`QAction`, `QKeySequence`, `QMenuBar`, `QToolBar`, `QStatusBar`, `QSplitter`) is already present in PySide6 6.11.0 installed in the project `.venv`. No new dependencies are required.

The recommended approach is to build incrementally in six steps: resizable splitter first (instantly testable, no logic change), then status bar labels, then menu and toolbar actions, then remove old buttons, then wire keyboard shortcuts. The key architectural insight is that a single `QAction` instance serves as the source of truth for a command across menu, toolbar, and keyboard shortcut simultaneously — creating one `QAction` is effectively a three-for-one migration for each button.

The primary risks are mechanical rather than conceptual: a wrong `QAction` import path (`QtGui` not `QtWidgets`), stale `setEnabled` call sites referencing removed button attributes, and macOS-specific menu role hijacking that moves actions to the system Application menu. All three are low-recovery-cost bugs that surface immediately with targeted testing. A strict "grep for old attribute names after each rename" discipline eliminates the stale-call-site risk.

## Key Findings

### Recommended Stack

No new packages are needed. The entire feature set is delivered using PySide6 6.11.0 already installed in `.venv`. The migration is a reorganisation of existing widgets using Qt's built-in `QMainWindow` facilities: `menuBar()` and `statusBar()` are auto-created by `QMainWindow` on first call, so there is not even a manual instantiation step for those.

**Core technologies:**
- **PySide6 6.11.0** (installed): All UI components — `QAction`, `QKeySequence`, `QMenuBar`, `QToolBar`, `QStatusBar`, `QSplitter` — all verified present in the installed environment.
- **Python 3.12** (in use): No compatibility issues.

**Critical import note:** `QAction` lives in `PySide6.QtGui`, not `PySide6.QtWidgets`. This changed between Qt5 and Qt6. Every tutorial written for PySide2/PyQt5 uses the wrong path.

### Expected Features

All features below are in scope for v3.0. There is no "defer to v2" for this milestone — it is a self-contained UI restructuring.

**Must have (table stakes):**
- File menu with Open Images and Exit (Ctrl+O, Ctrl+Q) — universal desktop convention
- Keyboard shortcut for Save (Ctrl+S mapped to Save Batch) — muscle memory expectation
- Toolbar with primary action buttons (Analyze, Auto-Optimize, Undo Mark, Clear) — one-click access
- Status bar showing batch name, image count, total cell count — always-visible app state
- Menu separators grouping related items — without them menus feel undifferentiated
- Delete key to remove selected image from list — keyboard-driven list management
- Undo Mark accessible from menu with Ctrl+Z — destructive action needs discoverability
- Window title continuing to reflect open batch name — standard document-oriented app pattern

**Should have (competitive/differentiator):**
- Analysis menu as a top-level menu (mirrors ImageJ conventions for scientific apps)
- Batch menu as a first-class top-level menu (signals batch workflow as primary — unusual in generic apps)
- Status bar showing progress during analysis (reuses existing `_on_progress` signal)
- Toolbar disabled-state management via `QAction.setEnabled()` (grayed-out = not available now)

**Defer (out of scope for this milestone):**
- Edit menu — no text editing semantics in this app
- Help menu / keyboard shortcuts dialog — Qt renders shortcuts inline in menus automatically
- Movable/floatable toolbar — disable with `setMovable(False)`; scientists don't rearrange toolbars
- Multi-level undo history — current data model doesn't support it; single-level Undo Mark is correct scope
- Recent files submenu — Open Batch dialog already serves this need

### Architecture Approach

The entire change is contained within `ui/main_window.py`. No new files are needed. The refactor adds two new methods (`_build_menus()` and `_build_toolbar()`) called from the existing `_build_ui()`, modifies the outer layout to use a horizontal `QSplitter` instead of a fixed-width panel, and replaces `_update_batch_buttons()` with `_update_actions()` that targets `QAction` objects instead of `QPushButton` objects. All other files (`param_panel.py`, `scaled_image_label.py`, `image_utils.py`, `batch_dialogs.py`) are untouched.

**Major components:**
1. **`QAction` instances (new)** — one per command; shared between `QMenu` and `QToolBar`; single `setEnabled()` call updates both surfaces simultaneously.
2. **`QMenuBar` with File / Batch / Analysis menus (new)** — auto-created via `self.menuBar()`; contains all current left-panel action buttons redistributed into logical groups.
3. **`QToolBar` (new)** — primary four actions (Analyze, Auto-Optimize, Undo Mark, Clear); `setMovable(False)` and `PreventContextMenu` to prevent accidental detachment or hiding.
4. **`QStatusBar` with permanent widgets (new)** — replaces `status_label` and `count_label` in the left panel; permanent `QLabel` widgets for batch name, image count, cell count; transient `showMessage()` for ephemeral feedback.
5. **Outer `QSplitter(Qt.Horizontal)` (new)** — wraps existing `left_scroll` and existing `right_splitter`; replaces `setFixedWidth(298)` with a draggable handle and a minimum width of 220px.
6. **`_update_actions()` refactored from `_update_batch_buttons()` (modified)** — centralised enabled/disabled state management; all 30+ individual call sites consolidated here.

### Critical Pitfalls

1. **`QAction` wrong import module** — `from PySide6.QtWidgets import QAction` raises `ImportError` at startup. Use `from PySide6.QtGui import QAction` always. Verify on first implementation commit.

2. **Stale `setEnabled` call sites on removed button attributes** — Python silently creates a new attribute rather than raising `AttributeError` when you call `setEnabled` on a non-existent object. After each button-to-action rename, run `grep -n "analyze_btn\|auto_optimize_btn\|undo_mark_btn\|save_batch_btn\|add_images_btn\|remove_image_btn\|re_analyze_btn\|export_csv_btn" ui/main_window.py` and expect zero results before proceeding.

3. **macOS menu role hijacking** — Qt's text heuristic automatically moves actions whose titles contain "about", "preferences", "settings", "quit", or "exit" to the macOS system Application menu. Actions disappear from the expected menu on macOS but are invisible on Windows/Linux. Set `action.setMenuRole(QAction.MenuRole.NoRole)` on all custom actions; allow the heuristic only for a deliberate "About" entry.

4. **Toolbar permanently hidden by right-click** — Qt toolbars show a "hide toolbar" context menu on right-click by default. Once hidden, there is no visible target for the context menu to restore it. Set `toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)` at toolbar creation.

5. **`QSplitter.restoreState()` called before window is shown** — Qt defers layout until the widget tree is visible; calling `restoreState` during `__init__` succeeds silently but the first layout pass on `show()` resets to defaults. Call `restoreState` after `window.show()` or defer via `QTimer.singleShot(0, ...)`.

## Implications for Roadmap

Based on research, the architecture supports a six-step incremental implementation. Each step is independently testable and leaves the app fully functional between steps.

### Phase 1: Resizable Sidebar
**Rationale:** Purely mechanical layout change with no logic impact. Immediately testable — drag the splitter handle and confirm it moves. No signal wiring needed. Establishes the outer layout that all subsequent steps build on.
**Delivers:** `QSplitter(Qt.Horizontal)` wrapping `left_scroll` and `right_splitter`. `setFixedWidth` calls removed. `setMinimumWidth(220)` set as collapse floor.
**Addresses:** Resizable sidebar requirement from FEATURES.md.
**Avoids:** Anti-Pattern 4 — keep existing `right_splitter` unchanged; only wrap it as a child of the new outer splitter.

### Phase 2: Status Bar Permanent Widgets
**Rationale:** The status bar is auto-created and already called in three places. Adding permanent widgets is additive — nothing is removed yet. Lets the status bar be validated before the panel labels are deleted.
**Delivers:** `_status_batch`, `_status_images`, `_status_cells` as `addPermanentWidget` labels. Status bar shows live batch name, image count, and total cell count.
**Addresses:** Status bar feature set (table stakes) from FEATURES.md.
**Avoids:** Anti-Pattern 3 — use `addPermanentWidget` for persistent data, `showMessage` only for ephemeral messages. Never call `showMessage` from worker threads; route through signals.

### Phase 3: Menu Bar and QAction Creation
**Rationale:** Define all `QAction` instances first (with `triggered.connect()` to existing slots) before adding them to any surface. Old `QPushButton` widgets stay temporarily so the app remains functional. Validates action wiring in isolation.
**Delivers:** `_build_menus()` method with File / Batch / Analysis menus fully populated. All keyboard shortcuts defined on actions via `QKeySequence`.
**Addresses:** Menu bar (P1), keyboard shortcuts (P1), and action-based enable/disable from FEATURES.md.
**Avoids:** Pitfall 1 (import from `QtGui`) and Pitfall 3 (macOS menu role — set `NoRole` on all custom actions).

### Phase 4: Toolbar
**Rationale:** Toolbar is a subset of already-created actions. Adding it after menu creation means actions are already wired and tested. Purely additive — no existing code changes.
**Delivers:** `_build_toolbar()` method. Four actions in toolbar: Analyze, Auto-Optimize, Undo Mark, Clear. `setMovable(False)` and `PreventContextMenu` set.
**Addresses:** Toolbar requirement (P1) and toolbar hide prevention (P1) from FEATURES.md.
**Avoids:** Pitfall 4 (toolbar right-click hide).

### Phase 5: Remove Old Buttons and Consolidate Enable/Disable
**Rationale:** This is the structural cleanup step. All `QPushButton` action widgets are removed from `_build_ui`. `_update_batch_buttons()` is refactored to `_update_actions()` targeting `QAction` objects. This is the riskiest step — the stale call-site pitfall surfaces here.
**Delivers:** Clean left panel with only `image_list` and `param_panel`. `_update_actions()` as the single authoritative enabled/disabled control point. `status_label` and `count_label` removed from sidebar.
**Addresses:** Left panel cleanup, action enable/disable correctness (P1) from FEATURES.md.
**Avoids:** Pitfall 2 (stale setEnabled call sites) — grep for old attribute names after each removal; expect zero results before proceeding.

### Phase 6: Keyboard Shortcut Verification and Polish
**Rationale:** Shortcuts are defined in Phase 3 but need end-to-end testing with focus in different widgets. Focus-dependent shortcut conflicts (Pitfall 7) only manifest during interactive testing.
**Delivers:** Verified shortcut behavior: Ctrl+O, Ctrl+S, Ctrl+Z, Delete (from list focus), Ctrl+Q. `Delete` key for Remove Image wired via `keyPressEvent` on `image_list` rather than global shortcut to avoid list widget interception.
**Addresses:** Keyboard shortcuts (P1) from FEATURES.md.
**Avoids:** Pitfall 7 (shortcut conflicts with QListWidget/QTableWidget built-in bindings).

### Phase Ordering Rationale

- Splitter comes first because it is the most isolated change and establishes the visual foundation without touching any logic.
- Status bar comes before menus because it is additive — permanent widgets appear alongside the existing left-panel labels, allowing comparison before deletion.
- Menu/action creation precedes button removal — this ensures the app always has a working control surface. Never remove a button before its action replacement is tested.
- Toolbar is added after menus because the actions are already wired; the toolbar is just an additional consumer of existing action instances.
- Button removal and `_update_actions()` refactor are deferred to Phase 5 specifically because the stale-call-site bug (Pitfall 2) is the highest likelihood defect, and isolating it to one phase makes it easier to diagnose.
- Shortcut testing is last because it requires an interactive session with focus management across all panels.

### Research Flags

Phases with standard patterns (no additional research needed):
- **Phase 1 (Splitter):** Fully documented Qt pattern. `QSplitter` API is stable and verified. Implementation is mechanical.
- **Phase 2 (Status Bar):** Already partially in use in the codebase. Additive change only.
- **Phase 3 (Menu Bar):** Well-documented Qt pattern; all API calls verified against installed PySide6 6.11.0.
- **Phase 4 (Toolbar):** Subset of Phase 3 actions. No new APIs.
- **Phase 5 (Button Removal):** Mechanical cleanup with clear verification via grep. No research needed, just discipline.
- **Phase 6 (Shortcuts):** Pitfall 7 is documented; mitigation strategy (keyPressEvent on list widget for Delete) is established.

**No phases require additional research-phase runs.** All APIs are verified against the installed environment and official Qt documentation.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All classes verified via runtime `hasattr` checks against PySide6 6.11.0 in `.venv`. No assumptions. |
| Features | HIGH | Qt/PySide6 UI patterns are well-established. Cross-validated against ImageJ and MIB scientific app conventions. Existing `main_window.py` read as ground truth for current button inventory. |
| Architecture | HIGH | Based on official Qt for Python docs and pythonguis.com tutorials. Build order respects actual Qt rendering lifecycle. All integration points identified from direct code analysis. |
| Pitfalls | HIGH | Pitfalls sourced from official Qt C++ and Python docs plus community-validated Qt Centre threads. PySide2-to-PySide6 `QAction` import change is documented in official migration guide. |

**Overall confidence: HIGH**

### Gaps to Address

- **QSplitter state persistence (QSettings):** Research identified the timing pitfall (`restoreState` before `show()`) but did not specify a QSettings key naming convention or whether the project already uses QSettings elsewhere. Check `main_window.py` for existing `QSettings` usage before implementing state persistence in Phase 1.
- **macOS test availability:** Pitfall 3 (menu role hijacking) is only observable on macOS. If development is on macOS, test immediately after Phase 3. If on Linux/Windows, flag for macOS validation before release.
- **`progress_bar` placement:** Research identifies it as "KEPT" but does not resolve whether it stays in the sidebar or moves to the status bar (`addWidget()`). Either is correct — decide during Phase 2 implementation based on visual preference.

## Sources

### Primary (HIGH confidence)
- Direct runtime verification against PySide6 6.11.0 in `/Users/ferar/fun/celulas/.venv` — all class/module memberships confirmed
- [PySide6.QtGui.QAction — Qt for Python official docs](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QAction.html)
- [PySide6.QtWidgets.QSplitter — Qt for Python official docs](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSplitter.html)
- [PySide6.QtWidgets.QMenuBar — Qt for Python official docs](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QMenuBar.html)
- [QMenuBar C++ docs — macOS heuristics section](https://doc.qt.io/qt-6/qmenubar.html)
- [Application Main Window — Qt for Python](https://doc.qt.io/qtforpython-6.8/overviews/qtwidgets-mainwindow.html)
- Existing `ui/main_window.py` — ground truth for current state

### Secondary (MEDIUM confidence)
- [PySide6 Toolbars, Menus & QAction — pythonguis.com](https://www.pythonguis.com/tutorials/pyside6-actions-toolbars-menus/) — PySide6-specific tutorial, widely referenced
- [Python and PyQt: Creating Menus, Toolbars, and Status Bars — Real Python](https://realpython.com/python-menus-toolbars/) — concepts consistent with official docs
- [ImageJ Analyze Menu](https://imagej.net/ij/docs/menus/analyze.html) — domain reference for scientific app menu conventions
- [Microscopy Image Browser features](https://mib.helsinki.fi/features_all.html) — peer scientific desktop app patterns
- [QToolBar right-click hide — qtcentre.org](https://qtcentre.org/threads/31498-QToolBar-How-do-you-suppress-the-right-click-menu-that-allows-hiding-the-toolbar)
- [QSplitter::restoreState() not working — qtcentre.org](https://www.qtcentre.org/threads/35300-QSplitter-restoreState()-not-working)
- [PySide2 vs PySide6 migration guide — pythonguis.com](https://www.pythonguis.com/faq/pyside2-vs-pyside6/)

---
*Research completed: 2026-03-30*
*Ready for roadmap: yes*
