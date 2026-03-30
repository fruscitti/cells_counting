"""Pure analysis functions for cell counting. No UI dependencies."""
import cv2
import itertools
import numpy as np


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
    centroids_list = []
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
                centroids_list.append((global_cx, global_cy))
                cv2.circle(viz, (global_cx, global_cy), 18, (0, 0, 255), 2)
                cv2.putText(viz, str(count), (global_cx - 10, global_cy - 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        else:
            count += 1
            cx, cy = centroids[i]
            centroids_list.append((int(cx), int(cy)))
            cv2.circle(viz, (int(cx), int(cy)), 18, (0, 0, 255), 2)
            cv2.putText(viz, str(count), (int(cx) - 10, int(cy) - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    return viz, count, centroids_list


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
        _, count, _ = process_image(img_small, b, a, bl, use_cleaning)
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
