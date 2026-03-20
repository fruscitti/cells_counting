import cv2
import itertools
import os
import pandas as pd
import numpy as np
import gradio as gr


def split_clumped_cells(thresh_roi, img_bgr_roi):
    """Split a single large blob using watershed. Returns (sub_count, list of (cx, cy) centroids)."""
    dist = cv2.distanceTransform(thresh_roi, cv2.DIST_L2, 5)
    _, sure_fg = cv2.threshold(dist, 0.5 * dist.max(), 255, 0)
    sure_fg = np.uint8(sure_fg)
    kernel = np.ones((3, 3), np.uint8)
    sure_bg = cv2.dilate(thresh_roi, kernel, iterations=3)
    unknown = cv2.subtract(sure_bg, sure_fg)
    num_markers, markers = cv2.connectedComponents(sure_fg)
    markers = np.int32(markers) + 1  # MUST be int32 for watershed
    markers[unknown == 255] = 0
    ws_img = img_bgr_roi.copy()
    if len(ws_img.shape) == 2:
        ws_img = cv2.cvtColor(ws_img, cv2.COLOR_GRAY2BGR)
    markers = cv2.watershed(ws_img, markers)
    centroids_list = []
    for label_id in range(2, markers.max() + 1):
        ys, xs = np.where(markers == label_id)
        if len(xs) > 0:
            centroids_list.append((int(xs.mean()), int(ys.mean())))
    return len(centroids_list), centroids_list


def process_image(img_bgr, brightness_threshold, min_cell_area, blur_strength, use_cleaning,
                  max_cell_area=500, use_tophat=False, tophat_kernel=50,
                  adaptive_block=99, adaptive_c=-5):
    green = img_bgr[:, :, 1]
    blurred = cv2.GaussianBlur(green, (blur_strength, blur_strength), 0)
    if use_tophat:
        k = int(tophat_kernel)
        bg_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        flat_field = cv2.morphologyEx(blurred, cv2.MORPH_TOPHAT, bg_kernel)
        block = int(adaptive_block)
        block = block if block % 2 == 1 else block + 1
        block = max(3, block)
        thresh = cv2.adaptiveThreshold(
            flat_field, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block,
            int(adaptive_c)
        )
    else:
        _, thresh = cv2.threshold(blurred, brightness_threshold, 255, cv2.THRESH_BINARY)
    if use_cleaning:
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    num_labels, labels_map, stats, centroids = cv2.connectedComponentsWithStats(thresh)
    count = 0
    viz = img_bgr.copy()
    h, w = img_bgr.shape[:2]
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < min_cell_area:
            continue
        if area > max_cell_area:
            # Extract ROI with 3px padding clamped to image bounds
            x0 = max(0, stats[i, cv2.CC_STAT_LEFT] - 3)
            y0 = max(0, stats[i, cv2.CC_STAT_TOP] - 3)
            x1 = min(w, stats[i, cv2.CC_STAT_LEFT] + stats[i, cv2.CC_STAT_WIDTH] + 3)
            y1 = min(h, stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT] + 3)
            thresh_roi = thresh[y0:y1, x0:x1]
            bgr_roi = img_bgr[y0:y1, x0:x1]
            sub_count, sub_centroids = split_clumped_cells(thresh_roi, bgr_roi)
            if sub_count == 0:
                sub_count = 1
                cx, cy = centroids[i]
                sub_centroids = [(int(cx) - x0, int(cy) - y0)]
            for local_cx, local_cy in sub_centroids:
                global_cx = x0 + local_cx
                global_cy = y0 + local_cy
                count += 1
                cv2.circle(viz, (global_cx, global_cy), 18, (0, 0, 255), 2)
                cv2.putText(viz, str(count), (global_cx - 10, global_cy - 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        else:
            count += 1
            cx, cy = centroids[i]
            cv2.circle(viz, (int(cx), int(cy)), 18, (0, 0, 255), 2)
            cv2.putText(viz, str(count), (int(cx) - 10, int(cy) - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    return viz, count


def optimize_parameters(img_bgr, use_cleaning=True):
    """Grid search for stable cell count parameters. Returns (best_brightness, best_min_area, best_blur, best_count)."""
    # Downsample large images for speed
    h, w = img_bgr.shape[:2]
    scale = 1.0
    if w > 1024:
        scale = 1024.0 / w
        img_small = cv2.resize(img_bgr, (1024, int(h * scale)))
    else:
        img_small = img_bgr

    brightness_vals = list(range(80, 200, 20))   # 6 values
    area_vals = list(range(10, 100, 15))          # 6 values
    blur_vals = list(range(3, 17, 2))             # 7 values

    results = {}
    for b, a, bl in itertools.product(brightness_vals, area_vals, blur_vals):
        # Grid search does NOT use max_cell_area / watershed (separate concern)
        _, count = process_image(img_small, b, a, bl, use_cleaning)
        results[(b, a, bl)] = count

    # Stability scoring: for each combo, count neighbors with same count
    best_score, best_params = -1, (120, 25, 9)
    for (b, a, bl), count in results.items():
        score = 0
        for db, da, dbl in itertools.product([-1, 0, 1], repeat=3):
            nb = b + db * 20
            na = a + da * 15
            nbl = bl + dbl * 2
            neighbor = (nb, na, nbl)
            if neighbor in results and results[neighbor] == count:
                score += 1
        if score > best_score or (score == best_score and
            abs(b - 120) + abs(a - 25) + abs(bl - 9) <
            abs(best_params[0] - 120) + abs(best_params[1] - 25) + abs(best_params[2] - 9)):
            best_score = score
            best_params = (b, a, bl)

    return best_params[0], best_params[1], best_params[2], results[best_params]


def draw_manual_marks(base_img_rgb, clicks):
    """Draw green manual marks on an RGB image copy. Returns new RGB image."""
    img = base_img_rgb.copy()
    for n, (x, y) in enumerate(clicks, start=1):
        cv2.circle(img, (x, y), 18, (0, 255, 0), 2)
        cv2.putText(img, f"M{n}", (x - 12, y - 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    return img


def run_analysis(files, brightness, min_area, max_area, blur, cleaning,
                 use_tophat, tophat_kernel, adaptive_block, adaptive_c):
    if not files:
        return [], pd.DataFrame(columns=["File", "Cell Count"]), {}, [], None, [], ""
    gallery, rows = [], []
    state = {"images": {}, "current_file": None}
    choices = []
    results_list = []
    for f in files:
        path = getattr(f, 'name', f)
        name = os.path.basename(path)
        img_bgr = cv2.imread(path)
        if img_bgr is None:
            continue
        orig_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        ann_bgr, count = process_image(img_bgr, brightness, min_area, blur, cleaning,
                                        max_cell_area=max_area, use_tophat=use_tophat,
                                        tophat_kernel=tophat_kernel,
                                        adaptive_block=adaptive_block, adaptive_c=adaptive_c)
        ann_rgb = cv2.cvtColor(ann_bgr, cv2.COLOR_BGR2RGB)
        gallery += [(orig_rgb, name), (ann_rgb, f"{name}: {count} cells")]
        rows.append([name, count])
        state["images"][name] = {
            "base_image": ann_rgb,  # annotated image in RGB, no manual marks
            "algo_count": count,
            "clicks": []
        }
        choices.append(name)
        results_list.append((orig_rgb, ann_rgb, name, count))
    df = pd.DataFrame(rows, columns=["File", "Cell Count"])
    if rows:
        total_text = f"**Total: {sum(r[1] for r in rows)} cells across {len(rows)} images**"
    else:
        total_text = ""
    return gallery, df, state, gr.update(choices=choices, value=None), None, results_list, total_text


def select_image(filename, state):
    """Load the selected image from state with all manual marks drawn."""
    if not filename or not state or filename not in state.get("images", {}):
        return None, 0, 0, 0, state
    state = dict(state)
    state["current_file"] = filename
    entry = state["images"][filename]
    img = draw_manual_marks(entry["base_image"], entry["clicks"])
    algo = entry["algo_count"]
    manual = len(entry["clicks"])
    total = algo + manual
    return img, algo, manual, total, state


def handle_click(evt: gr.SelectData, state):
    """Append a click to the current image and redraw."""
    if not state or not state.get("current_file"):
        return None, 0, 0, 0, state
    state = dict(state)
    fname = state["current_file"]
    entry = dict(state["images"][fname])
    entry["clicks"] = list(entry["clicks"])
    x, y = int(evt.index[0]), int(evt.index[1])
    entry["clicks"].append((x, y))
    state["images"] = dict(state["images"])
    state["images"][fname] = entry
    img = draw_manual_marks(entry["base_image"], entry["clicks"])
    algo = entry["algo_count"]
    manual = len(entry["clicks"])
    total = algo + manual
    return img, algo, manual, total, state


def undo_click(state):
    """Remove the last manual click from the current image."""
    if not state or not state.get("current_file"):
        return None, 0, 0, 0, state
    state = dict(state)
    fname = state["current_file"]
    entry = dict(state["images"][fname])
    entry["clicks"] = list(entry["clicks"])
    if entry["clicks"]:
        entry["clicks"].pop()
    state["images"] = dict(state["images"])
    state["images"][fname] = entry
    img = draw_manual_marks(entry["base_image"], entry["clicks"])
    algo = entry["algo_count"]
    manual = len(entry["clicks"])
    total = algo + manual
    return img, algo, manual, total, state


MAX_IMAGES = 20

_OG_HEAD = """
<meta property="og:title" content="Fluorescence Cell Counter" />
<meta property="og:description" content="Upload microscopy images to automatically detect and count fluorescent cells." />
<meta property="og:image" content="https://ferar.cloud/og-image.png" />
<meta property="og:url" content="https://ferar.cloud/cc" />
<meta name="twitter:card" content="summary_large_image" />
"""

with gr.Blocks(title="Fluorescence Cell Counter") as demo:
    gr.Markdown("## Fluorescence Cell Counter")

    annotation_state = gr.State({"images": {}, "current_file": None})
    results_state = gr.State([])

    with gr.Row():
        with gr.Column():
            files = gr.File(file_count="multiple", file_types=["image"], label="Upload Images")
            brightness = gr.Slider(0, 255, value=120, step=1, label="Brightness Threshold")
            min_area = gr.Slider(1, 500, value=25, step=1, label="Min Cell Area (px)")
            max_area = gr.Slider(50, 2000, value=500, step=10, label="Max Cell Area (watershed split)")
            blur = gr.Slider(1, 21, value=9, step=2, label="Blur Strength (odd)")
            cleaning = gr.Checkbox(value=True, label="Speckle Cleaning")
            use_tophat = gr.Checkbox(value=True, label="Flat-Field Correction (Top-Hat + Adaptive Threshold) — fixes uneven background")
            with gr.Group(visible=True) as tophat_group:
                tophat_kernel = gr.Slider(10, 100, value=50, step=5, label="Top-Hat Kernel Size (larger = removes broader background gradient)")
                adaptive_block = gr.Slider(11, 199, value=99, step=2, label="Adaptive Block Size (cover 1 cell + background, must be odd)")
                adaptive_c = gr.Slider(-20, 0, value=-5, step=1, label="Adaptive Constant C (more negative = stricter, fewer false positives)")
            with gr.Row():
                analyze_btn = gr.Button("Analyze", variant="primary")
                auto_opt_btn = gr.Button("Auto-Optimize")
                clear_btn = gr.ClearButton(
                    [files, brightness, min_area, max_area, blur, cleaning],
                    value="Clear"
                )
        with gr.Column():
            view_radio = gr.Radio(["Gallery", "Side-by-side"], value="Gallery", label="View")
            total_md = gr.Markdown("")
            gallery = gr.Gallery(label="Results (original | annotated)", columns=2)

            # Pre-built side-by-side rows (shown/hidden by view toggle)
            sbs_rows = []
            sbs_orig_imgs = []
            sbs_ann_imgs = []
            with gr.Column(visible=False) as sbs_container:
                for _i in range(MAX_IMAGES):
                    with gr.Row(visible=False) as _row:
                        _orig = gr.Image(interactive=False, show_label=True)
                        _ann = gr.Image(interactive=False, show_label=True)
                    sbs_rows.append(_row)
                    sbs_orig_imgs.append(_orig)
                    sbs_ann_imgs.append(_ann)

            dataframe = gr.Dataframe(headers=["File", "Cell Count"])

    gr.Markdown("### Manual Annotation (click on the image to mark missed cells)")
    with gr.Row():
        dropdown = gr.Dropdown(label="Select image to annotate", choices=[], interactive=True)
    with gr.Row():
        click_image = gr.Image(label="Click to add cells", interactive=False)
    with gr.Row():
        algo_count = gr.Number(label="Algorithm Count", interactive=False)
        manual_count = gr.Number(label="Manual Additions", interactive=False)
        total_count = gr.Number(label="Total", interactive=False)
    undo_btn = gr.Button("Undo Last Click")

    # Toggle flat-field controls visibility
    use_tophat.change(
        lambda v: gr.update(visible=v),
        inputs=[use_tophat],
        outputs=[tophat_group]
    )

    # Wire analyze button
    analyze_btn.click(
        run_analysis,
        inputs=[files, brightness, min_area, max_area, blur, cleaning,
                use_tophat, tophat_kernel, adaptive_block, adaptive_c],
        outputs=[gallery, dataframe, annotation_state, dropdown, click_image, results_state, total_md]
    )

    # Toggle between gallery and side-by-side view
    def switch_view(v, results):
        is_sbs = v == "Side-by-side"
        row_updates, orig_updates, ann_updates = [], [], []
        for i in range(MAX_IMAGES):
            if is_sbs and i < len(results):
                orig, ann, name, count = results[i]
                row_updates.append(gr.update(visible=True))
                orig_updates.append(gr.update(value=orig, label=f"{name} (original)"))
                ann_updates.append(gr.update(value=ann, label=f"{name}: {count} cells"))
            else:
                row_updates.append(gr.update(visible=False))
                orig_updates.append(gr.update(value=None))
                ann_updates.append(gr.update(value=None))
        return ([gr.update(visible=not is_sbs), gr.update(visible=is_sbs)]
                + row_updates + orig_updates + ann_updates)

    view_radio.change(
        switch_view,
        inputs=[view_radio, results_state],
        outputs=[gallery, sbs_container] + sbs_rows + sbs_orig_imgs + sbs_ann_imgs,
        show_progress="full"
    )

    # Wire auto-optimize button
    def auto_optimize(files, cleaning):
        if not files:
            gr.Warning("Please upload at least one image first.")
            return gr.update(), gr.update(), gr.update()
        path = getattr(files[0], 'name', files[0])
        img_bgr = cv2.imread(path)
        if img_bgr is None:
            gr.Warning("Could not read the first image.")
            return gr.update(), gr.update(), gr.update()
        b, a, bl, count = optimize_parameters(img_bgr, use_cleaning=cleaning)
        gr.Info(f"Suggested: brightness={b}, area={a}, blur={bl} (found {count} cells)")
        return gr.update(value=b), gr.update(value=a), gr.update(value=bl)

    auto_opt_btn.click(
        auto_optimize,
        inputs=[files, cleaning],
        outputs=[brightness, min_area, blur]
    )

    # Wire dropdown selection
    dropdown.change(
        select_image,
        inputs=[dropdown, annotation_state],
        outputs=[click_image, algo_count, manual_count, total_count, annotation_state]
    )

    # Wire image click
    click_image.select(
        handle_click,
        inputs=[annotation_state],
        outputs=[click_image, algo_count, manual_count, total_count, annotation_state]
    )

    # Wire undo button
    undo_btn.click(
        undo_click,
        inputs=[annotation_state],
        outputs=[click_image, algo_count, manual_count, total_count, annotation_state]
    )

    # Clear also resets annotation state, dropdown, click image, counts, results, total
    clear_btn.add([gallery, dataframe, annotation_state, dropdown, click_image,
                   algo_count, manual_count, total_count, total_md, results_state,
                   view_radio])

from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
demo.app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["127.0.0.1", "::1"])

if __name__ == "__main__":
    demo.launch(root_path="/cc", favicon_path="static/favicon.png", head=_OG_HEAD)
