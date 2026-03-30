---
phase: 3
slug: batch-management
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-qt |
| **Config file** | `pytest.ini` (exists: `qt_api = pyside6`, `testpaths = tests`) |
| **Quick run command** | `pytest tests/test_batch_manager.py -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_batch_manager.py -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 3.1 | 0 | BATCH-02–06, BMGR-02–05, BMGR-07 | unit stubs | `pytest tests/test_batch_manager.py -x -q` | ❌ W0 | ⬜ pending |
| 3-01-02 | 3.1 | 0 | BATCH-01, BMGR-01, BMGR-06 | unit stubs | `pytest tests/test_batch_ui.py -x -q` | ❌ W0 | ⬜ pending |
| 3-01-03 | 3.1 | 1 | BATCH-02 | unit | `pytest tests/test_batch_manager.py::test_save_creates_folder -x` | ❌ W0 | ⬜ pending |
| 3-01-04 | 3.1 | 1 | BATCH-03 | unit | `pytest tests/test_batch_manager.py::test_manifest_has_all_params -x` | ❌ W0 | ⬜ pending |
| 3-01-05 | 3.1 | 1 | BATCH-04 | unit | `pytest tests/test_batch_manager.py::test_marks_roundtrip -x` | ❌ W0 | ⬜ pending |
| 3-01-06 | 3.1 | 1 | BATCH-05 | unit | `pytest tests/test_batch_manager.py::test_atomic_write -x` | ❌ W0 | ⬜ pending |
| 3-01-07 | 3.1 | 1 | BATCH-06 | unit | `pytest tests/test_batch_manager.py::test_unique_name -x` | ❌ W0 | ⬜ pending |
| 3-01-08 | 3.1 | 1 | BMGR-02 | unit | `pytest tests/test_batch_manager.py::test_load_batch -x` | ❌ W0 | ⬜ pending |
| 3-01-09 | 3.1 | 1 | BMGR-03 | unit | `pytest tests/test_batch_manager.py::test_missing_image_status -x` | ❌ W0 | ⬜ pending |
| 3-01-10 | 3.1 | 2 | BATCH-01 | unit | `pytest tests/test_batch_ui.py::test_save_batch_button -x` | ❌ W0 | ⬜ pending |
| 3-01-11 | 3.1 | 2 | BMGR-01 | unit | `pytest tests/test_batch_ui.py::test_open_batch_dialog -x` | ❌ W0 | ⬜ pending |
| 3-02-01 | 3.2 | 1 | BMGR-04 | unit | `pytest tests/test_batch_manager.py::test_add_images -x` | ❌ W0 | ⬜ pending |
| 3-02-02 | 3.2 | 1 | BMGR-05 | unit | `pytest tests/test_batch_manager.py::test_remove_image_no_delete -x` | ❌ W0 | ⬜ pending |
| 3-02-03 | 3.2 | 1 | BMGR-07 | unit | `pytest tests/test_batch_manager.py::test_export_csv_columns -x` | ❌ W0 | ⬜ pending |
| 3-02-04 | 3.2 | 2 | BMGR-06 | unit | `pytest tests/test_batch_ui.py::test_reanalyze_preserves_marks -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_batch_manager.py` — stubs for BATCH-02–06, BMGR-02–05, BMGR-07 (pure Python, no Qt)
- [ ] `tests/test_batch_ui.py` — stubs for BATCH-01, BMGR-01, BMGR-06 (requires `qtbot`)

*Existing infrastructure (`pytest.ini`, `conftest.py`, `qtbot` fixture, `QT_QPA_PLATFORM=offscreen`) already established. No new installs needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Batch folder visible in Finder/Explorer | BATCH-02 | File system visual check | After "Save Batch", open `batches/` dir and verify folder + manifest.json + images exist |
| Missing image warning shown in dialog | BMGR-03 | Qt dialog rendering | Open a batch where one image file is deleted; verify warning appears in Open Batch dialog |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
