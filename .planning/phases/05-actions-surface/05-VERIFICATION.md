---
phase: 05-actions-surface
verified: 2026-03-30T00:00:00Z
status: passed
score: 7/7 must-haves verified
re_verification: false
---

# Phase 05: Actions Surface Verification Report

**Phase Goal:** Replace hidden QPushButtons with shared QAction instances, add a proper menu bar and toolbar, and centralize enable/disable logic
**Verified:** 2026-03-30
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | File menu contains Open Images, Open Batch, Save Batch, Export CSV, Exit in that order | VERIFIED | `_build_menu_bar()` at line 81 adds actions in exact order; `test_file_menu_actions` passes |
| 2 | Batch menu contains Add Images, Remove Image, Re-Analyze in that order | VERIFIED | `_build_menu_bar()` at line 93; `test_batch_menu_actions` passes |
| 3 | Analysis menu contains Analyze, Auto-Optimize, Undo Mark, Clear All in that order | VERIFIED | `_build_menu_bar()` at line 98; `test_analysis_menu_actions` passes |
| 4 | Toolbar shows Analyze, Auto-Optimize, Undo Mark, Clear All as text-only buttons | VERIFIED | `_build_toolbar()` at line 104 with `Qt.ToolButtonTextOnly`; `test_toolbar_actions` passes |
| 5 | Toolbar cannot be moved or hidden via right-click | VERIFIED | `toolbar.setMovable(False)` and `toolbar.setContextMenuPolicy(Qt.PreventContextMenu)` at lines 107-108; `test_toolbar_exists_and_locked` passes |
| 6 | Menu items and toolbar buttons share the same QAction instance | VERIFIED | Same `self.act_*` instances added to both menu and toolbar; `test_menu_toolbar_same_action` passes (identity check with `is`) |
| 7 | Disabling a QAction grays out both the menu item and toolbar button simultaneously | VERIFIED | Single `act_analyze.setEnabled(False)` affects both; `test_action_enable_disable_sync` passes |

**Score:** 7/7 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `ui/main_window.py` | QAction definitions, menu bar, toolbar, migrated enable/disable | VERIFIED | Contains `_build_actions()`, `_build_menu_bar()`, `_build_toolbar()`, `_update_action_states()`; 41 `act_*.setEnabled` call sites; 12 `MenuRole.NoRole` occurrences |
| `tests/test_main_window.py` | Tests for menu bar, toolbar, action sync | VERIFIED | Contains `test_menu_bar_exists`, `test_file_menu_actions`, `test_batch_menu_actions`, `test_analysis_menu_actions`, `test_toolbar_exists_and_locked`, `test_toolbar_actions`, `test_menu_toolbar_same_action`, `test_action_enable_disable_sync` — all 8 pass |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `_build_actions()` | menu bar and toolbar | same `self.act_*` instance added to both | WIRED | Lines 86-113: all 12 `act_*` instances added to menus; 4 added to toolbar using same objects |
| `_build_actions()` | existing slot methods | `triggered.connect(self._on_*)` | WIRED | Lines 318-329: all 12 actions connected to slots via `triggered.connect` |
| `setEnabled` call sites | QAction instances | `self.act_*.setEnabled()` replaces `self.*_btn.setEnabled()` | WIRED | `grep -c "act_.*\.setEnabled"` = 41; `grep -c "_btn\.setEnabled"` = 0; no old button references remain |

---

### Data-Flow Trace (Level 4)

Not applicable — this phase produces no data-rendering components. The artifacts are UI structure (menus, toolbar, QAction definitions) and enable/disable control logic, not data pipelines.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All menu/toolbar/action tests pass | `.venv/bin/python -m pytest tests/test_main_window.py -v` | 20 passed, 1 pre-existing failure (`test_total_count`) | PASS |
| No old `_btn.setEnabled` call sites remain | `grep -c "_btn\.setEnabled" ui/main_window.py` | 0 | PASS |
| All 12 actions have MenuRole.NoRole | `grep "MenuRole.NoRole" ui/main_window.py \| wc -l` | 12 | PASS |
| Toolbar is locked (setMovable) | `grep -c "setMovable(False)" ui/main_window.py` | 1 | PASS |
| `_update_batch_buttons` fully renamed | `grep -c "_update_batch_buttons" ui/main_window.py` | 0 | PASS |
| 41 migrated action enable/disable sites | `grep -c "act_.*\.setEnabled" ui/main_window.py` | 41 | PASS |
| No lingering old button definitions | grep for `open_btn\|analyze_btn\|...` (excluding zoom) | 0 matches | PASS |

Note: `test_total_count` was already failing before Phase 5 due to a pre-existing mismatch in `process_image` return-value count. It is out of scope for this phase and does not affect goal achievement.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| MENU-01 | 05-01-PLAN.md | File menu with correct items | SATISFIED | `test_file_menu_actions` passes; `_build_menu_bar()` verified |
| MENU-02 | 05-01-PLAN.md | Batch menu with correct items | SATISFIED | `test_batch_menu_actions` passes |
| MENU-03 | 05-01-PLAN.md | Analysis menu with correct items | SATISFIED | `test_analysis_menu_actions` passes |
| MENU-04 | 05-01-PLAN.md | Disabling action grays out both menu and toolbar | SATISFIED | `test_action_enable_disable_sync` passes; single QAction is single source of truth |
| TOOL-01 | 05-01-PLAN.md | Toolbar has correct 4 analysis actions | SATISFIED | `test_toolbar_actions` passes |
| TOOL-02 | 05-01-PLAN.md | Toolbar is non-movable and non-hideable | SATISFIED | `test_toolbar_exists_and_locked` passes |
| TOOL-03 | 05-01-PLAN.md | Menu and toolbar share same QAction instance | SATISFIED | `test_menu_toolbar_same_action` passes (identity check) |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/test_main_window.py` | 51 | `ann_bgr, count = process_image(...)` expects 2 return values but function returns more | Info (pre-existing) | Only `test_total_count` fails; pre-dates Phase 5; out of scope |

No Phase 5 anti-patterns found. All `setVisible(False)` occurrences in `main_window.py` are for `self.progress_bar`, not button-hiding.

---

### Human Verification Required

None — all observable truths are verified programmatically through the passing test suite and grep checks.

---

### Gaps Summary

No gaps. All 7 must-have truths are fully verified. The phase goal is achieved:

- 12 shared QAction instances defined in `_build_actions()` with `MenuRole.NoRole`
- Menu bar with File (5 items), Batch (3 items), Analysis (4 items) built in `_build_menu_bar()`
- Locked toolbar with 4 analysis actions built in `_build_toolbar()`
- All 12 actions wired to existing slot methods via `triggered.connect`
- All ~25 enable/disable sites migrated from `*_btn.setEnabled()` to `act_*.setEnabled()` (41 total call sites)
- Old QPushButton definitions and `setVisible(False)` hiding loop removed
- `_update_batch_buttons` renamed to `_update_action_states`; `_disable_batch_buttons_during_analysis` renamed to `_disable_actions_during_analysis`
- 20 of 21 tests pass; sole failure is a pre-existing issue unrelated to this phase

---

_Verified: 2026-03-30_
_Verifier: Claude (gsd-verifier)_
