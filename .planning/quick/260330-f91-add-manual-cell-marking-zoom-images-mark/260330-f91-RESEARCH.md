# Quick Task: Add Manual Cell Marking with Zoom — Research

**Researched:** 2026-03-30
**Domain:** PySide6 Qt desktop — image zoom + click-to-mark interaction
**Confidence:** HIGH (all findings from direct codebase inspection)

---

## What Already Exists

The app is a **PySide6 desktop app** (not web/Gradio). Entry point is `app.py`. `main.py` is the old Gradio web version left untouched.

### Manual marking is already half-built

| Feature | Status | Location |
|---------|--------|----------|
| Click-to-mark on annotated image | DONE | `ScaledImageLabel.mousePressEvent` emits `clicked(orig_x, orig_y)` |
| Coordinate mapping (screen → original pixels) | DONE | `ScaledImageLabel.mousePressEvent` — divides by scale factor |
| Mark storage in memory | DONE | `_images[fn]["manual_marks"]` list of `(x, y)` tuples |
| Draw marks on image | DONE | `analysis_core.draw_manual_marks()` — green circles, labels M1/M2/... |
| Undo last mark | DONE | `_on_undo_mark()` in MainWindow |
| Save marks with batch | DONE | `BatchManager.save_batch()` + `update_manifest()` — stored as JSON lists |
| Restore marks on batch open | DONE | `_load_batch_from_path()` restores from manifest |
| CSV export includes manual count | DONE | `BatchManager.export_csv()` — columns: total_count, algo_count, manual_count |

**What is NOT built:** Zoom in/out on the image display.

---

## The Missing Feature: Zoom

### Current display architecture

`ScaledImageLabel` (a `QLabel` subclass) scales the pixmap to fit the widget via `paintEvent`. It always fits-to-widget — no pan, no zoom. Clicking correctly maps screen coordinates back to original image pixels (already handles the scale ratio).

Key code in `ScaledImageLabel.paintEvent`:
```python
scaled = self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
x = (self.width() - scaled.width()) // 2
y = (self.height() - scaled.height()) // 2
painter.drawPixmap(x, y, scaled)
```

And in `mousePressEvent`, coordinate mapping already handles arbitrary scale:
```python
orig_x = int(img_x * self._pixmap.width() / scaled.width())
orig_y = int(img_y * self._pixmap.height() / scaled.height())
```

### Two valid zoom approaches in Qt/PySide6

**Option A: Scale the stored pixmap artificially (zoom factor on ScaledImageLabel)**

Add a `_zoom` float (default 1.0) to `ScaledImageLabel`. In `paintEvent`, multiply the fit-scaled size by `_zoom`. If `_zoom > 1.0`, the scaled image exceeds the widget — clip via a scroll offset or just center and let Qt clip. In `mousePressEvent`, the existing ratio math works unchanged because `scaled.width()` naturally reflects the zoom.

Pros: minimal changes, no new widget type.
Cons: no scrolling when zoomed in — edges of image become unreachable unless panning is also added.

**Option B: Wrap in QScrollArea + zoom by scaling displayed pixmap**

Put `ScaledImageLabel` inside a `QScrollArea`. When zoomed, set the label's fixed size to `original_size * zoom_factor` and call `setPixmap` with a version scaled to that size. Scrollbars appear automatically. `mousePressEvent` coordinate math still works.

Pros: full pan via scroll when zoomed in — can reach any cell.
Cons: requires minor layout change (insert QScrollArea in `main_window._build_ui`).

**Recommendation: Option B (QScrollArea)** — scientists need to scroll to mark cells at edges of a zoomed image. Without scrolling, zoom is nearly useless for the task.

### Coordinate correctness with zoom

The existing `mousePressEvent` math is already zoom-agnostic:
```python
orig_x = int(img_x * self._pixmap.width() / scaled.width())
```
`self._pixmap` is always the original-resolution image. `scaled.width()` is whatever size was rendered. As long as both values are correct, the mapping is exact regardless of zoom level. No coordinate logic needs changing.

---

## Implementation Plan

### 1. Add zoom state to ScaledImageLabel

```python
self._zoom = 1.0  # 1.0 = fit-to-widget

def zoom_in(self):  self._zoom = min(self._zoom * 1.25, 8.0); self.update()
def zoom_out(self): self._zoom = max(self._zoom / 1.25, 1.0); self.update()
def zoom_reset(self): self._zoom = 1.0; self.update()
```

In `paintEvent`, when `_zoom > 1.0`, compute a fixed displayed size and use it:
```python
fit_w, fit_h = ... # current fit-to-widget calculation
disp_w = int(fit_w * self._zoom)
disp_h = int(fit_h * self._zoom)
# If label has fixed size set to (disp_w, disp_h), scrollarea handles clipping
```

### 2. Wrap annotated_label in QScrollArea in MainWindow._build_ui

```python
from PySide6.QtWidgets import QScrollArea
self.annotated_scroll = QScrollArea()
self.annotated_scroll.setWidgetResizable(False)
self.annotated_label = ScaledImageLabel(click_enabled=True)
self.annotated_scroll.setWidget(self.annotated_label)
images_layout.addWidget(self.annotated_scroll)
```

When zoomed, call `self.annotated_label.setFixedSize(disp_w, disp_h)` so the scroll area activates its scrollbars.

### 3. Zoom controls

Add three buttons to the left panel:
- "Zoom In" — calls `annotated_label.zoom_in()`
- "Zoom Out" — calls `annotated_label.zoom_out()`
- "Zoom Reset" — calls `annotated_label.zoom_reset()`

Or use `QWheelEvent` on `ScaledImageLabel` for mouse-wheel zoom (more natural, same coordinate safety).

**Wheel zoom approach** (preferred — no extra buttons):
```python
def wheelEvent(self, event):
    delta = event.angleDelta().y()
    if delta > 0:
        self.zoom_in()
    elif delta < 0:
        self.zoom_out()
```

---

## Persistence: Already Done

Marks are already stored in `manifest.json` as:
```json
"manual_marks": [[x1, y1], [x2, y2]]
```

`load_batch()` normalizes them back to Python tuples. No changes needed to the persistence layer.

---

## Pitfalls

### Pitfall 1: Zoom on original_label too?

The task says "zoom images" (plural). If both labels zoom together, the coordinate mapping only matters for `annotated_label` (which receives clicks). The original label can zoom independently for visual inspection. Keep zoom state separate per label.

### Pitfall 2: setFixedSize vs setMinimumSize for scroll activation

`QScrollArea` only shows scrollbars when its child widget is larger than the viewport. Must call `setFixedSize(w, h)` or `resize(w, h)` on the label — not `setMinimumSize`. Using `setWidgetResizable(True)` defeats zoom (it auto-scales back to fit).

### Pitfall 3: Zoom resets on image switch

When `_on_image_selected` fires and calls `setPixmap`, the zoom level should reset to 1.0 (fit-to-widget) so the new image is fully visible. Call `zoom_reset()` in `_on_image_selected`.

### Pitfall 4: Click offset when scrolled

When inside a `QScrollArea`, `event.position()` in `mousePressEvent` is relative to the label widget, not the scroll viewport. This is correct — no adjustment needed. Qt delivers mouse events to the widget, so coordinates are already in label-space.

---

## What Does NOT Need to Change

- `analysis_core.draw_manual_marks()` — unchanged
- `BatchManager` — unchanged (marks already saved/restored)
- `_on_annotated_click`, `_on_undo_mark`, `_redraw_annotated` — unchanged
- Coordinate mapping math in `ScaledImageLabel.mousePressEvent` — unchanged

---

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Current state of manual marking | HIGH | Direct code inspection |
| QScrollArea + zoom approach | HIGH | Standard PySide6 pattern |
| Coordinate mapping safety | HIGH | Math verified in existing code |
| No persistence changes needed | HIGH | BatchManager already handles marks |
