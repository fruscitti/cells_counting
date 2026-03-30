---
phase: 2
slug: desktop-gui
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-29
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-qt 4.5.0 |
| **Config file** | `pytest.ini` |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 0 | APP-01 | smoke | `pytest tests/test_app_launch.py -x` | Wave 0 | pending |
| 2-01-02 | 01 | 0 | APP-04 | unit | `pytest tests/test_app_launch.py::test_highdpi_policy -x` | Wave 0 | pending |
| 2-01-03 | 01 | 1 | APP-01-04 | unit | `pytest tests/test_app_launch.py -x` | Wave 0 | pending |
| 2-01-04 | 01 | 1 | ANAL-04 | unit | `pytest tests/test_scaled_image_label.py::test_aspect_ratio -x` | Wave 0 | pending |
| 2-01-05 | 01 | 1 | IMG-01 | unit | `pytest tests/test_main_window.py::test_file_filter -x` | Wave 0 | pending |
| 2-01-06 | 01 | 1 | IMG-02 | unit | `pytest tests/test_main_window.py::test_image_list_exists -x` | Wave 0 | pending |
| 2-01-07 | 01 | 1 | IMG-03 | unit | `pytest tests/test_main_window.py::test_image_selection -x` | Wave 0 | pending |
| 2-01-08 | 01 | 1 | ANAL-05 | unit | `pytest tests/test_main_window.py::test_count_label_initial -x` | Wave 0 | pending |
| 2-02-01 | 02 | 1 | PARAM-01 | unit | `pytest tests/test_param_panel.py::test_brightness_slider -x` | Wave 0 | pending |
| 2-02-02 | 02 | 1 | PARAM-03 | unit | `pytest tests/test_param_panel.py::test_blur_odd_enforcement -x` | Wave 0 | pending |
| 2-02-03 | 02 | 1 | PARAM-06 | unit | `pytest tests/test_param_panel.py::test_tophat_visibility -x` | Wave 0 | pending |
| 2-02-04 | 02 | 1 | PARAM-07 | unit | `pytest tests/test_param_panel.py::test_value_labels -x` | Wave 0 | pending |
| 2-02-05 | 02 | 1 | partial-update | unit | `pytest tests/test_param_panel.py::test_set_params_partial -x` | Wave 0 | pending |
| 2-02-06 | 02 | 2 | ANAL-02 | integration | `pytest tests/test_analysis_worker.py::test_background_thread -x` | Wave 0 | pending |
| 2-02-07 | 02 | 2 | ANAL-03 | integration | `pytest tests/test_analysis_worker.py::test_progress_emitted -x` | Wave 0 | pending |
| 2-03-01 | 03 | 2 | MARK-01 | unit | `pytest tests/test_coordinate_mapping.py::test_click_mapping -x` | Wave 0 | pending |
| 2-03-02 | 03 | 2 | MARK-02 | unit | `pytest tests/test_coordinate_mapping.py::test_undo_mark -x` | Wave 0 | pending |
| 2-03-03 | 03 | 2 | MARK-03 | unit | `pytest tests/test_main_window.py::test_total_count -x` | Wave 0 | pending |
| 2-03-04 | 03 | 2 | CLR-01 | unit | `pytest tests/test_main_window.py::test_clear_resets -x` | Wave 0 | pending |
| 2-03-05 | 03 | 2 | D-07 | unit | `pytest tests/test_scaled_image_label.py::test_pixmap_conversion -x` | Wave 0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [x] `tests/conftest.py` — shared fixtures (sample image array, app instance via qtbot)
- [x] `tests/test_app_launch.py` — stubs for APP-01, APP-04
- [x] `tests/test_main_window.py` — stubs for IMG-01-03, ANAL-05, MARK-03, CLR-01
- [x] `tests/test_scaled_image_label.py` — stubs for ANAL-04, D-07
- [x] `tests/test_param_panel.py` — stubs for PARAM-01, PARAM-03, PARAM-06, PARAM-07, set_params_partial
- [x] `tests/test_analysis_worker.py` — stubs for ANAL-02, ANAL-03
- [x] `tests/test_coordinate_mapping.py` — stubs for MARK-01, MARK-02 (includes `import numpy as np`)
- [x] `pytest.ini` — project test config
- [x] `uv pip install pytest pytest-qt` — Wave 0 install

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Window renders correctly on macOS | APP-01 | Requires display | `python app.py` — verify window opens, layout looks correct |
| Side-by-side images scale on resize | ANAL-04 | Requires display + interaction | Resize window, verify both images scale proportionally |
| Auto-optimize updates all sliders | ANAL-07 | Requires real image + visual | Load a sample image, click Auto-Optimize, verify sliders update |
| Results table populates correctly | ANAL-06 | Requires real image + visual | Analyze image, verify filename + count appear in table |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter
- [x] `wave_0_complete: true` set in frontmatter

**Approval:** pending
