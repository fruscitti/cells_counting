# Pitfalls Research

**Domain:** PySide6 QMainWindow UI migration — adding QMenuBar, QToolBar, QStatusBar, migrating QPushButton to QAction, QSplitter sidebar persistence
**Researched:** 2026-03-30
**Confidence:** HIGH (verified against official Qt docs and pythonguis.com tutorials)

---

## Critical Pitfalls

### Pitfall 1: QAction Lives in QtGui, Not QtWidgets

**What goes wrong:**
`from PySide6.QtWidgets import QAction` raises an `ImportError`. The migration silently works in a Qt5/PySide2 codebase but fails on first run in PySide6.

**Why it happens:**
In Qt6, `QAction` was moved from `QtWidgets` to `QtGui` so it can be shared with non-widget (QML) applications. Every tutorial and Stack Overflow answer written for PySide2/PyQt5 uses the old import path. Muscle memory reproduces the bug.

**How to avoid:**
Always import from `QtGui`:
```python
from PySide6.QtGui import QAction, QKeySequence
```
Add a one-line import test to the very first implementation commit so the error surfaces at module load, not at runtime inside a handler.

**Warning signs:**
`ImportError: cannot import name 'QAction' from 'PySide6.QtWidgets'` on startup.

**Phase to address:** Implementation phase — first commit that introduces `QAction`.

---

### Pitfall 2: Duplicate Enabled/Disabled State — QPushButton Calls Left in Place

**What goes wrong:**
After migration the code still calls `self.analyze_btn.setEnabled(True/False)` in `_on_analyze`, `_on_analysis_finished`, `_on_clear`, `_update_batch_buttons`, and `_disable_batch_buttons_during_analysis`. When those buttons are replaced by QActions the attribute names change. Any site that still uses the old name silently does nothing (Python sets a new attribute on `self`) instead of raising `AttributeError`.

**Why it happens:**
The existing `main_window.py` has 30+ call sites spread across 12 methods that individually manage enabled state. During migration it is easy to rename the widget attribute but miss some of the call sites because they pass the same test (`setEnabled` is valid on any QWidget).

**How to avoid:**
- Replace button attributes with action attributes one-by-one and grep for the old attribute name immediately after each rename: `grep -n "analyze_btn\|auto_optimize_btn\|undo_mark_btn\|save_batch_btn" ui/main_window.py`
- Make `_update_batch_buttons()` the single authoritative place that sets enabled state for all actions. Remove every individual call site.
- Use `QAction.setEnabled()` — the same method signature as `QPushButton.setEnabled()`, so the migration is mechanical.
- The toolbar button and the menu item share one `QAction`, so a single `action.setEnabled(False)` grays out both simultaneously. This is the key benefit; exploit it fully.

**Warning signs:**
A toolbar button stays gray after analysis completes, or a menu item is clickable when it should not be. Enabled state is inconsistent between toolbar and menu for the same logical action.

**Phase to address:** Implementation phase — the `_update_batch_buttons()` refactor step.

---

### Pitfall 3: macOS Heuristic Menu Role Hijacking Custom Actions

**What goes wrong:**
On macOS, Qt scans every `QAction` title with a text heuristic and automatically moves matching items into the macOS system Application menu:

| Title pattern | Moved to |
|--------------|----------|
| Contains "about" | App menu > About |
| Contains "preferences", "settings", "options", "config", "setup" | App menu > Preferences |
| Contains "quit" or "exit" | App menu > Quit |

If you add an action named "Save Settings" or "About This Batch", it disappears from your File menu and reappears in the macOS App menu. The action still fires correctly, but users on macOS will not see it where you put it on Windows/Linux.

**Why it happens:**
`QAction::menuRole()` defaults to `TextHeuristicRole`. Qt applies this heuristic to conform to macOS HIG. Developers building on Windows or Linux never see the effect.

**How to avoid:**
For any action whose title could accidentally match the heuristic (e.g., "Export CSV" is safe; "Save Settings" is not), explicitly set:
```python
action.setMenuRole(QAction.MenuRole.NoRole)
```
As a safe default, set `NoRole` on every custom action and rely on the heuristic only for a deliberate "About Cell Counter" entry.

**Warning signs:**
An action visible in the menu on Windows/Linux is missing from that menu on macOS. The action still works if triggered by shortcut, but the menu item has vanished.

**Phase to address:** Implementation phase — immediately after the first macOS test run.

---

### Pitfall 4: QToolBar Right-Click Lets Users Permanently Hide It

**What goes wrong:**
By default, `QToolBar` shows a context menu on right-click that lets the user hide it. Once hidden there is no visible way to bring it back — the context menu target is gone. The user is stuck with no toolbar.

**Why it happens:**
Qt's built-in toolbar context menu only appears when the toolbar is visible. Hiding the toolbar removes the only access point for the context menu.

**How to avoid:**
Disable the default right-click menu on the toolbar:
```python
toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
```
Alternatively, add a View > Toolbar toggle in the menu bar so users can always restore it. For this app (single toolbar, no customization needed), `PreventContextMenu` is the correct and simplest fix.

**Warning signs:**
User right-clicks toolbar and hides it; toolbar does not come back; no menu entry to restore it.

**Phase to address:** Implementation phase — toolbar creation.

---

### Pitfall 5: QSplitter restoreState Called Before the Window Is Shown

**What goes wrong:**
Calling `splitter.restoreState(data)` during `__init__` (before `self.show()`) silently succeeds but has no lasting effect. The splitter recalculates geometry after the window becomes visible and resets to its default proportions. The saved sidebar width is discarded.

**Why it happens:**
Qt defers layout passes until the widget tree is visible. `restoreState` writes to internal size data, but the first layout pass triggered by `show()` recalculates from `sizeHint()` and `stretchFactor`, overwriting the restored values.

**How to avoid:**
Call `restoreState` after `show()`:
```python
window.show()
# Now safe to restore
splitter.restoreState(settings.value("splitter_state"))
```
Or defer via a zero-duration `QTimer.singleShot`:
```python
QTimer.singleShot(0, lambda: splitter.restoreState(saved_bytes))
```

**Warning signs:**
Sidebar width is always the default at startup regardless of what was saved. `restoreState` returns `True` (success) but the layout does not match the saved state.

**Phase to address:** Implementation phase — QSettings persistence step.

---

### Pitfall 6: QSplitter saveState Encodes Widget Count — Mismatches Silently Corrupt Layout

**What goes wrong:**
`QSplitter.saveState()` serialises the number of children. If a future refactor adds or removes a child widget from the splitter, `restoreState()` with old data returns `False` and leaves the splitter in an undefined state, potentially collapsing all panels to zero width.

**Why it happens:**
The state byte array is versioned with a widget count. Qt docs note: "Extra values in the list are ignored. If list contains too few values, the result is undefined." A mismatch is silent — no exception is raised.

**How to avoid:**
- Check the return value of `restoreState`. If `False`, fall back to explicit `setSizes()`:
  ```python
  if not splitter.restoreState(data):
      splitter.setSizes([280, 800])  # defaults
  ```
- Store the sidebar pixel width separately as an integer in QSettings as a fallback: `settings.setValue("sidebar_width", splitter.sizes()[0])`.

**Warning signs:**
After any refactor that changes splitter child count, startup shows all panels collapsed or default-sized even though settings contain data.

**Phase to address:** Implementation phase — QSettings persistence step; also as a guard whenever the splitter structure changes.

---

### Pitfall 7: Keyboard Shortcut Conflicts with QListWidget / QTableWidget Built-in Bindings

**What goes wrong:**
Standard Qt list and table widgets consume keyboard events before `QAction` shortcuts fire. Specifically:
- `Ctrl+A` — QListWidget/QTableWidget use it for "select all". If you add a QAction with `Ctrl+A` for "Add Images", it will sometimes fire and sometimes not depending on focus.
- `Delete` — QListWidget does not delete items by default, but `Delete` is consumed by focused list widgets on some platforms so a QAction shortcut for "Remove Image" may be intercepted.
- `Ctrl+Z` — QLineEdit and QTextEdit have built-in undo. If any edit widget has focus, `Ctrl+Z` as "Undo Mark" may undo text input instead of removing a cell mark.

**Why it happens:**
Qt routes keyboard events to the focused widget first. `QAction` shortcuts with `WindowShortcut` context only fire if the focused widget does not consume the key. `ApplicationShortcut` overrides all widgets, which causes its own problems (all windows fight for the key).

**How to avoid:**
- Assign shortcuts that have no standard widget binding: `Ctrl+O` (open), `Ctrl+S` (save), `Ctrl+Shift+A` (analyze), `Ctrl+E` (export), `Ctrl+Z` for undo-mark is safe only if there are no text-editing widgets with focus in the normal workflow.
- For "Delete to remove image" use the list widget's `currentItemChanged` to enable a QAction and handle the `Delete` key via `keyPressEvent` on the list widget rather than a global shortcut.
- Use `QKeySequence.StandardKey` enums (`QKeySequence.Open`, `QKeySequence.Save`) rather than raw strings — Qt maps them to the platform-correct key and documents platform behavior.

**Warning signs:**
A shortcut works when the image panel has focus but not when the list or table widget has focus. Ctrl+Z in a focused list unexpectedly triggers undo-mark.

**Phase to address:** Implementation phase — shortcut assignment step.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Keep both `self.analyze_btn` QPushButton and `self.analyze_action` QAction in parallel | Safer migration — old call sites still work | Double state management, buttons and menu items can drift out of sync | Never — remove buttons as each action is wired |
| Set `ApplicationShortcut` on all actions to avoid focus issues | Shortcuts always fire | Fights with QLineEdit undo, select-all; unexpected behavior when modal dialogs are open | Never for this app |
| Call `statusBar().showMessage()` from worker threads via direct call | Simpler code | Not thread-safe; Qt GUI must only be updated from the main thread | Never — always use signals |
| Skip `_update_batch_buttons()` refactor and call `action.setEnabled()` inline everywhere | Faster to write | Enabled state logic is scattered; easy to miss a site; bugs are hard to track | Never |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `QAction` + existing `QPushButton` call sites | Renaming the attribute but leaving `setEnabled` calls pointing at the old name — Python creates a new attribute silently | Grep for every old attribute name after each rename; run the app after each change |
| `QStatusBar.showMessage()` already called via `self.statusBar()` in existing code (lines 591, 781, 795) | Adding a new `status_label` QLabel in the left panel AND the status bar creates two sources of truth | Remove `self.status_label` from the left panel; route all status messages exclusively through `statusBar().showMessage()` |
| `QSplitter` wrapping the existing fixed-width `left_scroll` (298px) | Keeping `setFixedWidth` on the left scroll widget prevents the splitter from resizing it | Remove `setFixedWidth` and `setMinimumWidth` from the left panel widget when it moves into the splitter; set `setMinimumWidth` to a reasonable minimum (160px) instead |
| macOS `QMenuBar` and `statusBar()` | `menuBar()` and `statusBar()` are lazy-created; calling them before `_build_ui` does not crash but can create them in wrong order | Call `menuBar()` and `statusBar()` in `_build_ui` after `setCentralWidget`, or at minimum at the top of `_build_ui` before building menu contents |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Calling `_update_batch_buttons()` (or equivalent action enable/disable) inside `_on_image_done` signal which fires per-image | With 50+ images, UI freezes briefly as each image completes because enable/disable triggers a full UI repaint | Call `_update_batch_buttons()` only in `_on_analysis_finished`, not `_on_image_done` | Noticeable at ~20+ images |
| `QSplitter.saveState()` called on every `splitterMoved` signal | Writes QSettings on every pixel of drag — disk I/O on every mouse move | Connect to `splitterMoved` but debounce with `QTimer` (500ms), or save only on `closeEvent` | Immediate, especially on slow storage |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Toolbar hidden by right-click with no restore path | User loses all one-click access to Analyze, Undo, etc. | `toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)` |
| macOS: action title triggers heuristic move to App menu | Action disappears from expected location; scientist on macOS cannot find "Save Settings" | Explicitly set `action.setMenuRole(QAction.MenuRole.NoRole)` on all non-standard actions |
| Ampersand accelerator keys visible on macOS (e.g., "&File" shows as "&File" in some Qt versions) | Ugly menu text on macOS | Use ampersands normally — Qt handles rendering correctly on macOS; they just don't show as underlines, which is correct HIG |
| `QStatusBar` `showMessage` with timeout disappears while background analysis is still running | Status bar goes blank mid-analysis, user has no feedback | Use `showMessage` with `0` timeout (permanent) during analysis; set timed message only on completion events |

---

## "Looks Done But Isn't" Checklist

- [ ] **QAction enabled state:** Verify every enabled/disabled call site was migrated — run `grep -n "analyze_btn\|auto_optimize_btn\|undo_mark_btn\|save_batch_btn\|add_images_btn\|remove_image_btn\|re_analyze_btn\|export_csv_btn" ui/main_window.py` and expect zero results after migration.
- [ ] **macOS test:** Open the app on macOS and verify all menu items appear in the menus where placed, none have been moved to the Application menu unintentionally.
- [ ] **Toolbar hide prevention:** Right-click toolbar and confirm no context menu appears (or that a View > Toolbar toggle is available).
- [ ] **Splitter state restoration:** Close app with sidebar at custom width, reopen — sidebar must restore to that width, not the default.
- [ ] **Shortcut conflict test:** Click the image list to give it focus, then press each assigned shortcut — verify all fire correctly and none are swallowed by the list widget.
- [ ] **Status bar vs status label:** Confirm `self.status_label` (QLabel in left panel) is removed and all status updates flow through `self.statusBar().showMessage()`.
- [ ] **Thread safety:** Confirm `statusBar().showMessage()` is never called directly from a worker thread — only via signals.
- [ ] **QAction import:** Confirm `from PySide6.QtGui import QAction` — not `QtWidgets`.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| QAction import from wrong module | LOW | Update import line; 1-minute fix |
| Missed setEnabled call sites | LOW-MEDIUM | Grep for old attribute name; update each site; retest all enabled/disabled state transitions |
| macOS menu role hijack discovered late | LOW | Add `setMenuRole(NoRole)` to affected actions; no structural change needed |
| Toolbar permanently hidden by user before `PreventContextMenu` was set | LOW | Add `PreventContextMenu` call; released users can restore by editing QSettings file or via a keyboard shortcut |
| `restoreState` timing bug discovered after QSettings is wired | LOW | Wrap call in `QTimer.singleShot(0, ...)` or move after `show()`; no data loss |
| Splitter state mismatch after structural refactor | LOW | Clear QSettings key and let user resize; add `setSizes` fallback |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| QAction import module | Phase start — first action added | Import error on app launch |
| Duplicate enabled/disabled call sites | Toolbar/menu wiring step | Grep for old btn attribute names returns zero |
| macOS menu role hijacking | First macOS test run | All menu items appear in expected menus on macOS |
| Toolbar right-click hide | Toolbar creation step | Right-click toolbar produces no context menu |
| QSplitter restoreState timing | QSettings persistence step | Sidebar width survives app restart |
| QSplitter widget count mismatch | Any splitter structure change | `restoreState` return value checked; fallback `setSizes` in place |
| Keyboard shortcut conflicts | Shortcut assignment step | Each shortcut tested with each panel focused |

---

## Sources

- [PySide6 QAction — Qt for Python (official)](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QAction.html)
- [PySide6 QMenuBar — Qt for Python (official)](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QMenuBar.html)
- [QMenuBar C++ docs — macOS heuristics section (official)](https://doc.qt.io/qt-6/qmenubar.html)
- [PySide6 QSplitter — Qt for Python (official)](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSplitter.html)
- [QSplitter C++ docs (official)](https://doc.qt.io/qt-6/qsplitter.html)
- [PySide6 Toolbars, Menus & QAction — pythonguis.com (MEDIUM confidence)](https://www.pythonguis.com/tutorials/pyside6-actions-toolbars-menus/)
- [QToolBar right-click hide — disable context menu — qtcentre.org (MEDIUM confidence)](https://qtcentre.org/threads/31498-QToolBar-How-do-you-suppress-the-right-click-menu-that-allows-hiding-the-toolbar)
- [QSplitter::restoreState() not working — qtcentre.org (MEDIUM confidence)](https://www.qtcentre.org/threads/35300-QSplitter-restoreState()-not-working)
- [QAction setEnabled not working as expected — qtcentre.org (MEDIUM confidence)](https://www.qtcentre.org/threads/48083-QAction-setEnabled()-Not-Working-as-Expected)
- [PySide2 vs PySide6 migration guide — QAction import change (MEDIUM confidence)](https://www.pythonguis.com/faq/pyside2-vs-pyside6/)

---
*Pitfalls research for: PySide6 QMainWindow UI migration — menu bar, toolbar, QAction, QSplitter*
*Researched: 2026-03-30*
