# Phase 5: Actions Surface - Context

**Gathered:** 2026-03-30 (assumptions mode — user confirmed, no corrections)
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a menu bar (File / Batch / Analysis menus) and a persistent toolbar (Analyze, Auto-Optimize, Undo Mark, Clear All) wired via shared QAction instances. Every command the user previously accessed via hidden sidebar buttons is now reachable from the menu or toolbar. Single QAction per command = single enable/disable source of truth.

</domain>

<decisions>
## Implementation Decisions

### Menu Structure
- **D-01:** File menu: Open Images, Open Batch, Save Batch, Export CSV, Exit — in that order
- **D-02:** Batch menu: Add Images, Remove Image, Re-Analyze — in that order
- **D-03:** Analysis menu: Analyze, Auto-Optimize, Undo Mark, Clear All — in that order
- **D-04:** Apply `QAction.MenuRole.NoRole` to all custom actions — prevents macOS menu role hijacking (e.g., Quit getting moved to app menu)

### Toolbar
- **D-05:** Toolbar contains: Analyze, Auto-Optimize, Undo Mark, Clear All — text-only, no icons
- **D-06:** Toolbar is non-movable (`setMovable(False)`) and right-click context menu disabled (`PreventContextMenu`) — satisfies TOOL-02
- **D-07:** Toolbar added via `addToolBar(Qt.TopToolBarArea)` — top position, below menu bar

### QAction Architecture
- **D-08:** One QAction per command, created once in `_build_actions()`, stored as `self.act_open_images`, `self.act_analyze`, etc.
- **D-09:** Same QAction instance added to both menu and toolbar — satisfies TOOL-03 (single enable/disable source)
- **D-10:** All existing `btn.setEnabled()` calls migrate to `action.setEnabled()` — buttons are removed from layout entirely (they were already hidden in Phase 4)
- **D-11:** Import: `from PySide6.QtGui import QAction` — NOT QtWidgets (Qt6 change; wrong import = ImportError)

### Enable/Disable Migration
- **D-12:** Replace all `self.analyze_btn.setEnabled(x)` → `self.act_analyze.setEnabled(x)` etc. across all ~25 call sites
- **D-13:** `_update_batch_buttons()` method renamed to `_update_action_states()` and migrated to update actions instead of buttons
- **D-14:** Hidden buttons (`open_btn`, `analyze_btn`, etc.) removed from `_build_ui()` entirely — no `setVisible(False)` needed once actions exist

### Claude's Discretion
- Exact toolbar icon size / button padding
- Separator placement within menus (e.g., separator before Exit in File menu)
- Tooltip text on toolbar actions

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §MENU-01–04, TOOL-01–03 — exact acceptance criteria per requirement ID

### Prior phase implementation
- `ui/main_window.py` — all button definitions (lines ~54–111), `_connect_signals()` (~287–310), `_update_batch_buttons()` (~630–644), all `setEnabled` calls (~25 sites)
- `.planning/phases/04-layout-foundation/04-02-PLAN.md` — Phase 4 hid buttons; Phase 5 removes them

### Research already done (STATE.md)
- QAction is in `PySide6.QtGui`, not `PySide6.QtWidgets` — confirmed HIGH confidence
- QAction wires menu item + toolbar button + keyboard shortcut from one instance — confirmed
- `setMovable(False)` + `PreventContextMenu` for non-hideable toolbar — confirmed
- `QAction.MenuRole.NoRole` prevents macOS menu hijacking — confirmed

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- All slot methods (`_on_open_images`, `_on_analyze`, `_on_save_batch`, etc.) exist and work — actions connect to these directly via `triggered.connect()`
- `_update_batch_buttons()` at line ~630 already centralizes batch-related enable/disable logic — rename and migrate
- `_is_analyzing` flag already guards enable/disable for batch buttons — reuse in `_update_action_states()`

### Established Patterns
- `_build_ui()` / `_connect_signals()` split — new `_build_actions()` and `_build_menu_bar()` / `_build_toolbar()` follow same pattern
- All parameters and state stored on `self.*` — actions stored as `self.act_*` to follow naming

### Integration Points
- `_build_ui()`: remove hidden buttons, add `_build_actions()` call before menu/toolbar setup
- `_connect_signals()`: no changes needed — slot methods unchanged; action `triggered` signals connect to same slots
- `load_images()`: replace `self.analyze_btn.setEnabled(True)` → `self.act_analyze.setEnabled(True)`
- `_on_image_selected()`: replace `self.undo_mark_btn.setEnabled(...)` → `self.act_undo_mark.setEnabled(...)`
- `_on_annotated_click()` / `_on_undo_mark()`: same migration
- `_on_analyze()` / `_on_analysis_done()` / `_on_auto_optimize()`: same migration (~10 sites)
- `_update_batch_buttons()` → `_update_action_states()`: migrate all 6 batch actions

</code_context>

<specifics>
## Specific Ideas

- No icons — text-only toolbar is consistent with the current app style (scientific, minimal)
- User confirmed: "just plan it" — no additional preferences

</specifics>

<deferred>
## Deferred Ideas

- Keyboard shortcuts (Ctrl+O, Ctrl+S, etc.) — Phase 6 scope
- Removing old buttons from tests — Phase 6 cleanup scope

</deferred>

---

*Phase: 05-actions-surface*
*Context gathered: 2026-03-30*
