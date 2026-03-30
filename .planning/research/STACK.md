# Stack Research

**Domain:** PySide6 desktop app — menu bar, toolbar, status bar, keyboard shortcuts, resizable sidebar
**Researched:** 2026-03-30
**Confidence:** HIGH (all claims verified against PySide6 6.11.0 installed in .venv)

## Context: What Already Exists

`ui/main_window.py` is a `QMainWindow` subclass with:
- `QSplitter(Qt.Vertical)` on the right side (images + results table) — already in use
- Fixed-width left panel: `QScrollArea` with `setFixedWidth(298)` — this is what gets replaced
- `statusBar()` already called in 3 places (`showMessage(text, msec)`) — auto-created by Qt, no setup needed
- `QFont`, `QFileDialog`, `QDialog`, `QMessageBox` already imported from correct modules
- `QThreadPool` for background workers — no change needed

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| PySide6 | 6.11.0 (installed) | All UI components | Already installed and validated. All target APIs confirmed present. |
| Python | 3.12 | Language runtime | Already in use. |

### New APIs Needed for This Milestone

All classes below are already available in the installed PySide6 6.11.0 — no new `pip install` required.

| Class | Module | Purpose | Integration Point |
|-------|--------|---------|-------------------|
| `QAction` | `PySide6.QtGui` | Reusable command object with text, shortcut, statusTip, enabled state | Created once, added to both `QMenu` and `QToolBar` — single source of truth for each command |
| `QKeySequence` | `PySide6.QtGui` | Keyboard shortcut specification | Passed to `QAction.setShortcut()`. Use `QKeySequence.StandardKey.X` enum for platform-aware shortcuts (Cmd on macOS, Ctrl on Win/Linux) or `QKeySequence('Ctrl+S')` string form for custom keys. |
| `QMenuBar` | `PySide6.QtWidgets` | Application menu bar | `self.menuBar()` on `QMainWindow` auto-creates it — no manual instantiation needed. Call `self.menuBar().addMenu('&File')` to get a `QMenu`. |
| `QMenu` | `PySide6.QtWidgets` | Dropdown menu inside menu bar | Created via `menuBar().addMenu('name')`. Call `menu.addAction(action)` and `menu.addSeparator()`. |
| `QToolBar` | `PySide6.QtWidgets` | Persistent action buttons row | `self.addToolBar('name')` on `QMainWindow` creates and docks it at the top. Call `toolbar.addAction(action)` and `toolbar.addSeparator()`. |
| `QStatusBar` | `PySide6.QtWidgets` | Bottom status strip | `self.statusBar()` auto-creates it on first call — already used in `_on_save_batch`, `_on_reanalyze_finished`, `_on_export_csv`. Extend by calling `addPermanentWidget(QLabel)` for batch name / image count / cell count. |
| `QSplitter(Qt.Horizontal)` | `PySide6.QtWidgets` | Resizable sidebar | Replace `left_scroll.setFixedWidth(298)` + `main_layout.addWidget(left_scroll)` with a horizontal splitter: `outer = QSplitter(Qt.Horizontal); outer.addWidget(left_scroll); outer.addWidget(right_splitter)`. |

## Key API Patterns

### QAction — Create Once, Share Between Menu and Toolbar

```python
from PySide6.QtGui import QAction, QKeySequence

# In _build_ui or a dedicated _create_actions method:
self.analyze_action = QAction("Analyze", self)
self.analyze_action.setShortcut(QKeySequence("Ctrl+Return"))
self.analyze_action.setStatusTip("Analyze all loaded images")
self.analyze_action.setEnabled(False)
self.analyze_action.triggered.connect(self._on_analyze)
```

**Why create once, share**: If the same `QAction` instance is added to both a `QMenu` and a `QToolBar`, its `setEnabled(True/False)` state propagates to both automatically. No need to track `analyze_btn.setEnabled()` and `toolbar_analyze_btn.setEnabled()` separately.

**Migration note**: The existing `analyze_btn`, `undo_mark_btn`, etc. can be removed from the left panel. Their `setEnabled()` calls throughout the file should be replaced with `self.analyze_action.setEnabled()`.

### QKeySequence — Use StandardKey Enum for Platform Portability

```python
# Platform-aware (Cmd+O on macOS, Ctrl+O on Windows/Linux):
action.setShortcut(QKeySequence.StandardKey.Open)   # Open file
action.setShortcut(QKeySequence.StandardKey.Save)   # Save batch
action.setShortcut(QKeySequence.StandardKey.Delete) # Remove image
action.setShortcut(QKeySequence.StandardKey.Undo)   # Undo mark

# Custom shortcuts (not in StandardKey):
action.setShortcut(QKeySequence("Ctrl+Return"))     # Analyze
action.setShortcut(QKeySequence("Ctrl+Shift+O"))    # Open batch
```

**Verified StandardKeys**: `Open`, `Save`, `Delete`, `Undo`, `Quit`, `New`, `Close` — all confirmed present in `QKeySequence.StandardKey`.

### QMenuBar + QMenu — Auto-Created, Just Call addMenu

```python
# In _build_ui, AFTER setCentralWidget():
file_menu = self.menuBar().addMenu("&File")
file_menu.addAction(self.open_action)
file_menu.addSeparator()
file_menu.addAction(self.quit_action)

batch_menu = self.menuBar().addMenu("&Batch")
batch_menu.addAction(self.save_batch_action)
batch_menu.addAction(self.open_batch_action)
```

**No import of QMenuBar needed** if you only call `self.menuBar()`. Import `QMenu` if you need to type-hint or create submenus.

### QToolBar — addToolBar Creates and Docks It

```python
# In _build_ui:
toolbar = self.addToolBar("Main")
toolbar.setMovable(False)      # prevents undocking
toolbar.setFloatable(False)    # prevents floating window
toolbar.addAction(self.analyze_action)
toolbar.addAction(self.auto_optimize_action)
toolbar.addSeparator()
toolbar.addAction(self.undo_mark_action)
toolbar.addAction(self.clear_action)
```

**Note**: `toolbar.addAction(action)` where `action` is already in a menu — same instance, shared state.

### QStatusBar — Auto-Created, Extend with Permanent Widgets

```python
# In _build_ui, after setCentralWidget():
self._batch_status_label = QLabel("No batch open")
self._image_count_label = QLabel("0 images")
self._cell_count_status_label = QLabel("0 cells")

self.statusBar().addPermanentWidget(self._cell_count_status_label)
self.statusBar().addPermanentWidget(self._image_count_label)
self.statusBar().addPermanentWidget(self._batch_status_label)
```

**Permanent vs transient**: `addPermanentWidget` labels stay visible always (right-aligned). `showMessage(text, msec)` overlays temporary messages on the left — already working in the codebase. Both coexist without conflict.

**Migration note**: Replace `self.status_label = QLabel("Ready")` in the left panel and `self.count_label` with the status bar labels. The left panel gains the freed space for the image list and param sliders.

### QSplitter (Horizontal) — Replace Fixed-Width Left Panel

```python
# Replace in _build_ui:
# OLD:
#   left_scroll.setFixedWidth(298)
#   main_layout.addWidget(left_scroll)
#   main_layout.addWidget(right_splitter, stretch=1)

# NEW:
outer_splitter = QSplitter(Qt.Horizontal)
outer_splitter.addWidget(left_scroll)
outer_splitter.addWidget(right_splitter)
outer_splitter.setSizes([280, 900])           # initial pixel split
outer_splitter.setCollapsible(0, False)       # prevent sidebar collapsing to zero
outer_splitter.setHandleWidth(6)              # wider grab handle = easier resize
central = QWidget()
self.setCentralWidget(central)
main_layout = QHBoxLayout(central)
main_layout.setContentsMargins(0, 0, 0, 0)
main_layout.addWidget(outer_splitter)
```

**Remove `setFixedWidth`** calls on `left_panel` (line 48) and `left_scroll` (line 120-121). The splitter handles minimum size via `left_scroll.setMinimumWidth(220)` instead.

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| `QAction` shared across menu + toolbar | Separate `QPushButton` in toolbar | Buttons don't integrate with `QMenu`, don't auto-update enabled state from one place, no keyboard shortcut support |
| `QKeySequence.StandardKey.Open` enum | `QKeySequence('Ctrl+O')` string | StandardKey enum is platform-aware (uses Cmd on macOS). Use string form only when no matching StandardKey exists. |
| `self.statusBar()` (auto-created) | `QStatusBar()` instantiated manually + `self.setStatusBar(sb)` | Auto-creation is simpler and already implicitly used by existing `showMessage` calls |
| `QSplitter(Qt.Horizontal)` wrapping left+right | `QSizeGrip` on fixed panel | `QSplitter` is the Qt-native answer, supports `setSizes`, `saveState/restoreState`, min width enforcement |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `QShortcut` | Lower-level shortcut class. Creates shortcuts per-widget with extra boilerplate. | `QAction.setShortcut()` — shortcuts activate whenever the action is enabled, scoped to window |
| `QAction` from `PySide6.QtWidgets` | `QAction` is in `QtGui` in PySide6 6.x. Importing from `QtWidgets` will raise `ImportError`. | `from PySide6.QtGui import QAction` |
| `left_panel.setFixedWidth(278)` | Prevents user from resizing sidebar. Contradicts the resizable sidebar requirement. | Remove the call; set `left_scroll.setMinimumWidth(220)` instead |
| `left_scroll.setFixedWidth(298)` | Same reason — hard-coded prevents resizing. | Remove; let `QSplitter` manage the width |
| `self.status_label = QLabel("Ready")` (left panel) | Takes left panel space, duplicates status bar. | Move to `self.statusBar().showMessage()` for transient messages and `addPermanentWidget` labels for persistent info |
| `self.count_label = QLabel("Cell Count: 0")` (left panel) | Takes left panel space. | Move to `self.statusBar().addPermanentWidget(QLabel(...))` |
| Icon-only toolbar buttons | No icons are currently used in the project; adding an icon set adds dependencies and asset management complexity. | Text-only toolbar (`toolbar.addAction(action)` renders the action's text) |

## Module Import Summary

```python
# Additions to the existing import block in main_window.py:
from PySide6.QtWidgets import (
    # ... existing imports ...
    # QToolBar, QStatusBar, QMenuBar, QMenu already in QtWidgets
    QToolBar,   # add
    # QMenuBar and QStatusBar are not needed if only accessed via self.menuBar() / self.statusBar()
)
from PySide6.QtGui import (
    QFont,          # already imported
    QAction,        # add — NOTE: QtGui, not QtWidgets
    QKeySequence,   # add
)
```

## Version Compatibility

| Package | Version | Notes |
|---------|---------|-------|
| PySide6 | 6.11.0 | Installed. `QAction` is in `QtGui` (moved from `QtWidgets` in PySide6 6.x vs PyQt5). All verified APIs stable since 6.0. |
| Python | 3.12 | Compatible. No issues. |

## Sources

- Direct runtime verification against PySide6 6.11.0 in `/Users/ferar/fun/celulas/.venv` — HIGH confidence
- `ui/main_window.py` read to identify exact integration points — HIGH confidence
- All class memberships (`QAction` in `QtGui`, `QToolBar`/`QStatusBar`/`QMenuBar`/`QMenu` in `QtWidgets`) confirmed via `hasattr` checks — HIGH confidence

---
*Stack research for: PySide6 menu bar, toolbar, status bar, keyboard shortcuts, resizable sidebar*
*Researched: 2026-03-30*
