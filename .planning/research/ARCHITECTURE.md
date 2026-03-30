# Architecture Research

**Domain:** PySide6 QMainWindow refactor — menu bar, toolbar, status bar, resizable sidebar
**Researched:** 2026-03-30
**Confidence:** HIGH (based on official Qt for Python docs and verified PySide6 tutorials)

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│  QMainWindow                                                          │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  QMenuBar  [File | Batch | Analysis]                           │  │
│  └────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  QToolBar  [Analyze | Auto-Optimize | Undo Mark | Clear]       │  │
│  └────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Central Widget                                                 │  │
│  │  ┌──────────────────┐  ┌───────────────────────────────────┐  │  │
│  │  │ QSplitter (H)    │  │                                   │  │  │
│  │  │ ┌──────────────┐ │  │   right_splitter (V, existing)    │  │  │
│  │  │ │  Left Sidebar│ │  │   ┌───────────────────────────┐  │  │  │
│  │  │ │  QScrollArea │ │  │   │ Side-by-side images        │  │  │  │
│  │  │ │  ┌──────────┐│ │  │   │ (orig + annotated)         │  │  │  │
│  │  │ │  │image_list││ │  │   └───────────────────────────┘  │  │  │
│  │  │ │  │          ││ │  │   ┌───────────────────────────┐  │  │  │
│  │  │ │  │param_panel│ │  │   │ results_table              │  │  │  │
│  │  │ │  └──────────┘│ │  │   └───────────────────────────┘  │  │  │
│  │  │ └──────────────┘ │  │                                   │  │  │
│  │  └──────────────────┘  └───────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  QStatusBar  [Batch: name | Images: N | Cells: N]              │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Status |
|-----------|----------------|--------|
| `QMenuBar` | Full command surface: File, Batch, Analysis menus | NEW |
| `QToolBar` | One-click access to primary actions (subset of menu items) | NEW |
| `QStatusBar` | Persistent bottom bar: batch name, image count, cell count | NEW — replaces `status_label` + `count_label` |
| Outer `QSplitter` (Horizontal) | Replaces fixed `left_scroll` (298px). Makes sidebar resizable | NEW — replaces `setFixedWidth(278)` |
| Left sidebar content | `image_list` + `param_panel` stacked vertically | UNCHANGED (moved into splitter) |
| `right_splitter` (Vertical, existing) | Images on top, results table on bottom | UNCHANGED |
| `ScaledImageLabel` (x2) | Original + annotated image display | UNCHANGED |
| `ParamPanel` | Parameter sliders — stays in sidebar | UNCHANGED |
| `QProgressBar` | Analysis progress indicator | UNCHANGED — stays in sidebar or status bar |
| `QListWidget` (image_list) | Image file list | UNCHANGED |
| `QTableWidget` (results_table) | Per-file cell count results | UNCHANGED |

## Recommended Project Structure

```
ui/
├── main_window.py          # Modified: _build_ui(), _build_menus(), _build_toolbar()
├── param_panel.py          # Unchanged
├── scaled_image_label.py   # Unchanged
├── image_utils.py          # Unchanged
└── batch_dialogs.py        # Unchanged
```

No new files are required. All changes are contained within `main_window.py`.

### Structure Rationale

- **No new files:** The refactor is purely a layout transformation inside `MainWindow`. All business logic, slots, and workers remain untouched.
- **`param_panel.py` stays as-is:** It is a self-contained `QWidget` that slides into the new sidebar without modification.

## Architectural Patterns

### Pattern 1: QAction as the Single Source of Truth

**What:** Create one `QAction` instance per command. Add the same instance to both a `QMenu` and a `QToolBar`. Both surfaces share enabled/disabled state, shortcut, icon, and signal connection automatically.

**When to use:** Every button that moves into the menu bar. This is the canonical Qt pattern — not optional.

**Trade-offs:** Slightly more setup per action than a `QPushButton`, but enables keyboard shortcuts, status tip on hover, and consistent enable/disable with zero extra wiring.

**Example:**
```python
# In _build_menus() / _build_toolbar() — called from _build_ui()
self.act_analyze = QAction("Analyze", self)
self.act_analyze.setShortcut(QKeySequence("Ctrl+Return"))
self.act_analyze.setStatusTip("Run cell detection on all loaded images")
self.act_analyze.setEnabled(False)
self.act_analyze.triggered.connect(self._on_analyze)

# Same instance added to both surfaces
analysis_menu.addAction(self.act_analyze)   # menu
self.toolbar.addAction(self.act_analyze)    # toolbar
```

**Migration rule:** Every `QPushButton` with a non-trivial handler becomes a `QAction`. The `clicked.connect(slot)` becomes `triggered.connect(slot)`. The `btn.setEnabled(x)` becomes `action.setEnabled(x)`.

### Pattern 2: Outer QSplitter Replaces Fixed Left Panel

**What:** Wrap the existing `left_scroll` (sidebar) and `right_splitter` (images+table) in a horizontal `QSplitter`. Remove `setFixedWidth(278)` and `setFixedWidth(298)`.

**When to use:** Any time a panel needs to be user-resizable rather than fixed.

**Trade-offs:** Adds ~5 lines of code. The splitter handle is draggable by default; no extra event handling needed.

**Example:**
```python
# _build_ui() — replace the manual QHBoxLayout approach
outer_splitter = QSplitter(Qt.Horizontal)

left_sidebar = QWidget()           # same content as before
left_scroll = QScrollArea()
left_scroll.setWidgetResizable(True)
left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
left_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
left_scroll.setWidget(left_sidebar)
left_scroll.setMinimumWidth(220)   # collapse floor, not a fixed width

outer_splitter.addWidget(left_scroll)
outer_splitter.addWidget(right_splitter)   # existing right_splitter unchanged
outer_splitter.setStretchFactor(0, 0)      # sidebar: don't stretch on resize
outer_splitter.setStretchFactor(1, 1)      # image area: takes all extra space
outer_splitter.setSizes([280, 900])        # initial sizes (approximate)

self.setCentralWidget(outer_splitter)
```

### Pattern 3: QStatusBar Replaces Inline Labels

**What:** `QMainWindow.statusBar()` returns the built-in status bar (auto-created on first call). Use `showMessage()` for transient messages and permanent widgets for persistent data.

**When to use:** Replacing `status_label` ("Ready", "Analyzing...", "Analysis complete") and `count_label` ("Cell Count: N").

**Trade-offs:** `showMessage(text, msec)` auto-clears after timeout. Permanent widgets (added via `addPermanentWidget()`) stay visible. Mix both for the right UX.

**Example:**
```python
# In _build_ui() — after all other widgets
self._status_batch = QLabel("No batch")
self._status_images = QLabel("Images: 0")
self._status_cells = QLabel("Cells: 0")

sb = self.statusBar()
sb.addPermanentWidget(self._status_batch)
sb.addPermanentWidget(QLabel("|"))   # separator
sb.addPermanentWidget(self._status_images)
sb.addPermanentWidget(QLabel("|"))
sb.addPermanentWidget(self._status_cells)

# Transient messages (replaces status_label.setText):
self.statusBar().showMessage("Analyzing...", 0)   # 0 = persistent until next call
self.statusBar().showMessage("Analysis complete", 3000)  # auto-clears after 3s
```

## Data Flow

### QAction Enable/Disable Flow

```
State change (images loaded, batch opened, analysis running)
    ↓
_update_batch_buttons() / load_images() / _on_analysis_finished()
    ↓
self.act_analyze.setEnabled(True/False)
    ↓
Both QMenu item AND QToolBar button reflect the change automatically
    (no separate toolbar button enable/disable calls needed)
```

### Action Trigger Flow

```
User clicks toolbar button   OR   User selects menu item   OR   Keyboard shortcut
    ↓                                     ↓                            ↓
                     QAction.triggered signal (single connection)
                                    ↓
                          slot method (_on_analyze, etc.)
                                    ↓
                          status bar + progress bar update
```

### Status Bar Update Flow

```
Any slot that changes meaningful state:
    _on_analyze()           → showMessage("Analyzing...")
    _on_analysis_finished() → showMessage("Analysis complete", 3000)
                              _status_cells.setText(f"Cells: {total}")
    load_images()           → _status_images.setText(f"Images: {N}")
    _load_batch_from_path() → _status_batch.setText(f"Batch: {name}")
    _on_clear()             → clear all permanent labels + showMessage("Ready")
```

## Integration Points

### New vs Modified vs Unchanged

| Element | Change Type | Notes |
|---------|-------------|-------|
| `_build_ui()` | MODIFIED | Outer QSplitter replaces QHBoxLayout + fixed widths |
| `_build_menus()` | NEW METHOD | Called from `_build_ui()`. Creates QMenuBar + QMenu + QAction instances |
| `_build_toolbar()` | NEW METHOD | Called from `_build_ui()`. Adds subset of QActions to QToolBar |
| `_connect_signals()` | REMOVED (or emptied) | All signals move to `_build_menus()` / `_build_toolbar()` via `triggered.connect()` at QAction creation time |
| `_update_batch_buttons()` | MODIFIED | References switch from `self.analyze_btn.setEnabled(x)` to `self.act_analyze.setEnabled(x)` |
| `_disable_batch_buttons_during_analysis()` | MODIFIED | Same — action references replace button references |
| `_on_clear()` | MODIFIED | Clears status bar permanent labels; `status_label.setText` calls replaced |
| `_on_progress()` | MODIFIED | Calls `self.statusBar().showMessage(...)` instead of `status_label.setText` |
| `_on_analyze()` / `_on_analysis_finished()` | MODIFIED | Status updates go to status bar |
| `_on_optimize_result()` | MODIFIED | Status update goes to status bar |
| `_on_save_batch()` / batch slots | MODIFIED | `self.statusBar().showMessage(...)` calls already exist — keep them |
| `status_label` (QLabel) | REMOVED | Replaced by status bar |
| `count_label` (QLabel) | REMOVED | Replaced by `_status_cells` permanent widget in status bar |
| All `QPushButton` action buttons | REMOVED | Replaced by QAction instances |
| Zoom `QPushButton` widgets | KEPT | These are inline controls for the image panels, not top-level commands |
| `progress_bar` (QProgressBar) | KEPT | Stays in sidebar or moves to status bar (`addWidget()`) |
| `param_panel` (ParamPanel) | UNCHANGED | No modifications needed |
| `image_list` (QListWidget) | UNCHANGED | Moves into new splitter sidebar |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `QAction` → slot | `triggered` signal | Same signal regardless of invocation path (menu, toolbar, shortcut) |
| `MainWindow` → `QStatusBar` | Direct method calls | `showMessage()`, `_status_cells.setText()` |
| `MainWindow` → `ParamPanel` | `get_params()` / `set_params()` | Unchanged |
| `MainWindow` → workers | `QThreadPool` / signals | Unchanged |
| `MainWindow` → `BatchManager` | Direct calls | Unchanged |

## Suggested Build Order

The following order respects dependencies and allows incremental testing:

1. **Replace fixed left panel with outer QSplitter** — mechanical, immediately testable. Remove `setFixedWidth` calls, wrap sidebar and `right_splitter` in `QSplitter(Qt.Horizontal)`. All existing buttons still work.

2. **Add QStatusBar permanent widgets** — add `_status_batch`, `_status_images`, `_status_cells` as permanent widgets. Replace `status_label.setText` and `count_label.setText` calls throughout. Remove `status_label` and `count_label` widgets from sidebar.

3. **Create QAction instances in `_build_menus()`** — define all actions with shortcuts, status tips, and `triggered.connect()`. Build `QMenuBar` with File / Batch / Analysis menus. Keep old `QPushButton` widgets temporarily so the app still functions.

4. **Create QToolBar in `_build_toolbar()`** — add primary action subset. Still works alongside old buttons.

5. **Remove old QPushButton widgets** — remove action buttons from `_build_ui()` and `_connect_signals()`. Update `_update_batch_buttons()` and `_disable_batch_buttons_during_analysis()` to reference actions.

6. **Add keyboard shortcuts** — verify Ctrl+O, Ctrl+S, Delete (remove image), Ctrl+Z (undo mark), etc. work end-to-end.

## Anti-Patterns

### Anti-Pattern 1: Duplicating Signal Connections

**What people do:** Create a `QAction` but also keep the old `QPushButton`, connecting both `btn.clicked` and `action.triggered` to the same slot.

**Why it's wrong:** Double-fires the slot. Leaves dead UI in place that confuses layout.

**Do this instead:** Remove the `QPushButton` entirely when its `QAction` is created. The action IS the button — in menu, toolbar, and keyboard.

### Anti-Pattern 2: Per-Surface Enable/Disable

**What people do:** Call `toolbar_btn.setEnabled(x)` AND `menu_item.setEnabled(x)` separately, treating them as different controls.

**Why it's wrong:** They get out of sync. When you call `action.setEnabled(x)`, Qt propagates to all surfaces that host the action automatically.

**Do this instead:** Call `self.act_analyze.setEnabled(x)` once. Menu and toolbar both update.

### Anti-Pattern 3: Permanent Status Bar Messages via showMessage

**What people do:** Use `showMessage("Cells: 42")` for persistent data like cell counts.

**Why it's wrong:** `showMessage` is transient — it can be overwritten by any other `showMessage` call (including Qt's own hover-tip display). Persistent data disappears.

**Do this instead:** Use `addPermanentWidget(QLabel(...))` for batch name, image count, and cell count. Use `showMessage` only for ephemeral feedback like "Saved" or "Analysis complete".

### Anti-Pattern 4: Nested QSplitter Confusion

**What people do:** Replace the existing `right_splitter` (vertical) instead of wrapping it.

**Why it's wrong:** The right-side vertical splitter (images top, table bottom) is already working. It only needs to be placed as the second child of the new outer horizontal splitter.

**Do this instead:** Keep `right_splitter` unchanged. Add it as `outer_splitter.addWidget(right_splitter)`.

## Sources

- [PySide6 Toolbars, Menus & QAction — pythonguis.com](https://www.pythonguis.com/tutorials/pyside6-actions-toolbars-menus/) — HIGH confidence, verified against official Qt docs
- [PySide6.QtGui.QAction — Qt for Python official docs](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QAction.html) — HIGH confidence
- [PySide6.QtWidgets.QSplitter — Qt for Python official docs](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSplitter.html) — HIGH confidence
- [PySide6.QtWidgets.QMenuBar — Qt for Python official docs](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QMenuBar.html) — HIGH confidence
- Existing `ui/main_window.py` — direct code analysis

---
*Architecture research for: PySide6 QMainWindow v3.0 UI Redesign (menu bar, toolbar, status bar, resizable sidebar)*
*Researched: 2026-03-30*
