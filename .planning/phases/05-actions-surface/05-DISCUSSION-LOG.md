# Phase 5: Actions Surface - Discussion Log (Assumptions Mode)

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in CONTEXT.md — this log preserves the analysis.

**Date:** 2026-03-30
**Phase:** 05-actions-surface
**Mode:** assumptions (user confirmed with no corrections)
**Areas analyzed:** Menu Structure, Toolbar, QAction Architecture, Enable/Disable Migration

## Assumptions Presented

### Menu Structure
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| File/Batch/Analysis menu grouping matches ROADMAP | Confident | ROADMAP.md Phase 5 success criteria, REQUIREMENTS.md MENU-01–03 |
| QAction.MenuRole.NoRole needed on macOS | Confident | STATE.md research findings (HIGH confidence) |

### Toolbar
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| Text-only toolbar (no icons) | Likely | No icons exist anywhere in app; scientific/minimal style |
| Toolbar content: Analyze, Auto-Optimize, Undo Mark, Clear All | Confident | ROADMAP.md TOOL-01 |
| setMovable(False) + PreventContextMenu | Confident | STATE.md research findings, REQUIREMENTS.md TOOL-02 |

### QAction Architecture
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| QAction from PySide6.QtGui (not QtWidgets) | Confident | STATE.md research findings (HIGH confidence, Qt6 change) |
| One QAction instance shared between menu + toolbar | Confident | REQUIREMENTS.md TOOL-03; STATE.md research |

### Enable/Disable Migration
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| ~25 btn.setEnabled() call sites need migration | Confident | grep of main_window.py shows 25 sites |
| _update_batch_buttons() rename to _update_action_states() | Likely | Natural rename; centralizes all action state management |
| Buttons removed entirely (not just hidden) | Confident | Phase 4 already hid them; Phase 5 removes them |

## Corrections Made

No corrections — user selected "just plan it" (option 3), confirming all assumptions.

## External Research

No external research needed — all technical questions already answered in STATE.md v3.0 research findings (HIGH confidence).
