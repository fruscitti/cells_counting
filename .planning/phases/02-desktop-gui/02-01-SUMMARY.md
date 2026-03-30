---
phase: 02-desktop-gui
plan: "01"
subsystem: ui
tags: [pyside6, qt, python, opencv, pytest, pytest-qt]

# Dependency graph
requires: []
provides:
  - PySide6 desktop app scaffold with MainWindow, image loading, and side-by-side display
  - ScaledImageLabel widget with aspect-ratio-preserving paint and click signal
  - numpy_rgb_to_pixmap utility (thread-safe QImage.copy pattern)
  - pytest + pytest-qt test infrastructure with offscreen rendering
  - Test stubs for all 3 plans (Plans 01-03)
affects: [02-02-PLAN, 02-03-PLAN]

# Tech tracking
tech-stack:
  added: [PySide6 6.11.0, pytest 9.0.2, pytest-qt 4.5.0]
  patterns:
    - ScaledImageLabel subclasses QLabel, stores _pixmap, scales in paintEvent
    - numpy_rgb_to_pixmap uses QImage.copy() for thread safety (prevents segfault)
    - QApplication must exist before any QImage/QPixmap operations (enforced via qtbot)
    - MainWindow defers heavy imports inside main() to ensure QApplication pre-exists

key-files:
  created:
    - app.py
    - ui/__init__.py
    - ui/main_window.py
    - ui/scaled_image_label.py
    - ui/image_utils.py
    - pytest.ini
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_app_launch.py
    - tests/test_scaled_image_label.py
    - tests/test_main_window.py
    - tests/test_param_panel.py
    - tests/test_analysis_worker.py
    - tests/test_coordinate_mapping.py
  modified: []

key-decisions:
  - "qtbot fixture required for any test calling numpy_rgb_to_pixmap — QApplication must be active before QImage creation"
  - "ScaledImageLabel keeps _pixmap separate from QLabel.pixmap() to avoid Qt scaling interference"
  - "param_container is a placeholder QWidget — Plan 02 inserts ParamPanel into it"

patterns-established:
  - "ScaledImageLabel pattern: store _pixmap, override paintEvent with KeepAspectRatio scaled draw"
  - "Test isolation: conftest sets QT_QPA_PLATFORM=offscreen via os.environ.setdefault"
  - "MainWindow._images dict structure: {basename: {original_bgr, original_rgb, annotated_rgb, algo_count, manual_marks}}"

requirements-completed: [APP-01, APP-02, APP-03, APP-04, IMG-01, IMG-02, IMG-03, ANAL-04, ANAL-05]

# Metrics
duration: 4min
completed: 2026-03-30
---

# Phase 02 Plan 01: App Scaffold + Image Display Summary

**PySide6 Cell Counter window with file-dialog image loading, QListWidget navigation, side-by-side ScaledImageLabel display, and full pytest-qt test infrastructure**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-30T01:06:44Z
- **Completed:** 2026-03-30T01:09:52Z
- **Tasks:** 3
- **Files modified:** 14

## Accomplishments
- Runnable PySide6 app: `python app.py` opens "Cell Counter" window (1024x700 min size)
- ScaledImageLabel preserves aspect ratio on resize via custom paintEvent; emits click signal for Plan 03
- MainWindow wires file dialog, QListWidget, side-by-side image display, count label, and results table
- pytest-qt infrastructure with offscreen rendering; 10 tests pass, 10 skipped (Plan 02/03 stubs)

## Task Commits

1. **Task 01-01: Install dependencies + test infrastructure** - `32de4a4` (chore)
2. **Task 01-02: app.py, ScaledImageLabel, image utilities** - `13ff553` (feat)
3. **Task 01-03: MainWindow** - `1aa174e` (feat)

## Files Created/Modified
- `/Users/ferar/fun/celulas/app.py` - Entry point with HiDPI policy and MainWindow launch
- `/Users/ferar/fun/celulas/ui/__init__.py` - Package init
- `/Users/ferar/fun/celulas/ui/main_window.py` - MainWindow with full layout, image loading, list navigation
- `/Users/ferar/fun/celulas/ui/scaled_image_label.py` - Aspect-ratio-preserving image label with click signal
- `/Users/ferar/fun/celulas/ui/image_utils.py` - numpy_rgb_to_pixmap conversion (thread-safe)
- `/Users/ferar/fun/celulas/pytest.ini` - pytest config with qt_api=pyside6
- `/Users/ferar/fun/celulas/tests/conftest.py` - Shared fixtures (sample_rgb_array, main_window)
- `/Users/ferar/fun/celulas/tests/test_app_launch.py` - APP-01/02/03/04 tests
- `/Users/ferar/fun/celulas/tests/test_scaled_image_label.py` - ScaledImageLabel and pixmap conversion tests
- `/Users/ferar/fun/celulas/tests/test_main_window.py` - IMG-01/02/03 and ANAL-05 tests
- `/Users/ferar/fun/celulas/tests/test_param_panel.py` - Plan 02 stubs (all skipped)
- `/Users/ferar/fun/celulas/tests/test_analysis_worker.py` - Plan 02 stub (skipped)
- `/Users/ferar/fun/celulas/tests/test_coordinate_mapping.py` - Plan 03 stubs (skipped)

## Decisions Made
- qtbot added to test_pixmap_conversion: QApplication must be active before QImage can be created (otherwise abort/segfault)
- ScaledImageLabel stores `_pixmap` directly instead of using QLabel's built-in pixmap storage, to avoid Qt's default scaling interfering with the custom paintEvent logic
- param_container is an empty QWidget placeholder so Plan 02 can insert a ParamPanel widget without structural changes to MainWindow

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added qtbot to test_pixmap_conversion to prevent abort**
- **Found during:** Task 01-02 (test_scaled_image_label.py verification)
- **Issue:** test_pixmap_conversion called numpy_rgb_to_pixmap without an active QApplication, causing Fatal Python error: Aborted (exit code 134) when QImage was constructed
- **Fix:** Added `qtbot` parameter to test_pixmap_conversion — pytest-qt creates QApplication automatically when qtbot is active
- **Files modified:** tests/test_scaled_image_label.py
- **Verification:** `pytest tests/test_scaled_image_label.py -x -q` passes (3 tests)
- **Committed in:** 32de4a4 (Task 01-01 commit, bundled with test stubs)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Single essential fix for test correctness. No scope creep.

## Issues Encountered
None beyond the auto-fixed test abort above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 02 can insert ParamPanel into `self.param_container` in MainWindow
- Plan 02 can wire `self.analyze_btn` to a QRunnable worker
- Plan 03 can connect `self.original_label.clicked` signal for manual cell marking
- All test stubs for Plans 02 and 03 are in place and collectible without errors

## Self-Check: PASSED

- All 14 created files verified on disk
- All 3 task commits verified in git history (32de4a4, 13ff553, 1aa174e)
- `pytest tests/ -x -q` passes: 10 passed, 10 skipped

---
*Phase: 02-desktop-gui*
*Completed: 2026-03-30*
