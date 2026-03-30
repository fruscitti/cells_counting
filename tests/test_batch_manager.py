"""Unit tests for BatchManager — pure Python, no Qt required."""
import json
import numpy as np
import pytest

PARAMS = {
    "brightness_threshold": 120,
    "min_cell_area": 25,
    "blur_strength": 9,
    "max_cell_area": 500,
    "use_cleaning": True,
    "use_tophat": False,
    "tophat_kernel": 50,
    "adaptive_block": 99,
    "adaptive_c": -5,
}


def _make_images(with_annotated=True, manual_marks=None):
    """Helper to build a minimal _images dict like MainWindow uses."""
    original_bgr = np.zeros((50, 50, 3), dtype=np.uint8)
    original_rgb = np.zeros((50, 50, 3), dtype=np.uint8)
    annotated_rgb = np.zeros((50, 50, 3), dtype=np.uint8) if with_annotated else None
    return {
        "img1.png": {
            "original_bgr": original_bgr,
            "original_rgb": original_rgb,
            "annotated_rgb": annotated_rgb,
            "algo_count": 5,
            "manual_marks": manual_marks if manual_marks is not None else [],
        }
    }


def test_save_creates_folder(tmp_path):
    """BATCH-02: save_batch creates batches/<date>_<name>/ with manifest.json + image copies."""
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    images = _make_images()
    batch_dir = BatchManager.save_batch("test", images, PARAMS)
    assert batch_dir.exists(), "batch directory should exist"
    assert (batch_dir / "manifest.json").exists(), "manifest.json should exist"
    assert (batch_dir / "img1.png").exists(), "original image copy should exist"


def test_manifest_has_all_params(tmp_path):
    """BATCH-03: saved manifest['parameters'] contains all 9 keys from ParamPanel.DEFAULTS."""
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    images = _make_images()
    batch_dir = BatchManager.save_batch("params-test", images, PARAMS)
    with open(batch_dir / "manifest.json", encoding="utf-8") as f:
        manifest = json.load(f)
    saved_params = manifest["parameters"]
    for key in PARAMS:
        assert key in saved_params, f"parameter '{key}' missing from manifest"
    assert saved_params == PARAMS


def test_marks_roundtrip(tmp_path):
    """BATCH-04: manual_marks [[120, 88], [200, 150]] survive save+load as tuples."""
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    marks = [(120, 88), (200, 150)]
    images = _make_images(manual_marks=marks)
    batch_dir = BatchManager.save_batch("marks-test", images, PARAMS)
    manifest = BatchManager.load_batch(batch_dir)
    loaded_marks = manifest["images"][0]["manual_marks"]
    assert len(loaded_marks) == 2, "should have 2 marks"
    assert tuple(loaded_marks[0]) == (120, 88), "first mark should be (120, 88)"
    assert tuple(loaded_marks[1]) == (200, 150), "second mark should be (200, 150)"


def test_atomic_write(tmp_path):
    """BATCH-05: _atomic_write_manifest writes valid JSON; no .tmp files left behind."""
    from batch_manager import BatchManager
    batch_dir = tmp_path / "test_batch"
    batch_dir.mkdir()
    manifest = {"schema_version": 1, "name": "test", "images": [], "parameters": PARAMS}
    BatchManager._atomic_write_manifest(batch_dir, manifest)
    # Verify valid JSON was written
    with open(batch_dir / "manifest.json", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["schema_version"] == 1
    # Verify no .tmp files remain
    tmp_files = list(batch_dir.glob("*.tmp"))
    assert len(tmp_files) == 0, f"tmp files should not remain: {tmp_files}"


def test_unique_name(tmp_path):
    """BATCH-06: saving with same name twice produces two different folders (_2 suffix)."""
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    images = _make_images()
    dir1 = BatchManager.save_batch("test", images, PARAMS)
    dir2 = BatchManager.save_batch("test", images, PARAMS)
    assert dir1 != dir2, "two saves with same name should produce different directories"
    assert dir1.exists(), "first batch dir should exist"
    assert dir2.exists(), "second batch dir should exist"
    # Second folder name should end with _2
    assert dir2.name.endswith("_2"), f"second folder should end with _2, got: {dir2.name}"


def test_load_batch(tmp_path):
    """BMGR-02: load_batch returns manifest dict with correct schema_version, name, images, parameters."""
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    images = _make_images()
    batch_dir = BatchManager.save_batch("load-test", images, PARAMS)
    manifest = BatchManager.load_batch(batch_dir)
    assert manifest["schema_version"] == 1, "schema_version should be 1"
    assert manifest["name"] == "load-test", "name should be 'load-test'"
    assert "images" in manifest, "manifest should have 'images' key"
    assert "parameters" in manifest, "manifest should have 'parameters' key"
    assert len(manifest["images"]) == 1, "should have 1 image entry"
    assert manifest["images"][0]["filename"] == "img1.png"


def test_missing_image_status(tmp_path):
    """BMGR-03: load_batch sets status='missing' for entries where file does not exist on disk."""
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    images = _make_images()
    batch_dir = BatchManager.save_batch("missing-test", images, PARAMS)
    # Delete the image file to simulate missing
    (batch_dir / "img1.png").unlink()
    manifest = BatchManager.load_batch(batch_dir)
    assert manifest["images"][0]["status"] == "missing", "missing file should have status='missing'"


def test_list_batches(tmp_path):
    """list_batches returns sorted list of batch metadata dicts (name, path, created_at, image_count)."""
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    images = _make_images()
    BatchManager.save_batch("batch-a", images, PARAMS)
    BatchManager.save_batch("batch-b", images, PARAMS)
    batches = BatchManager.list_batches()
    assert len(batches) == 2, "should list 2 batches"
    for b in batches:
        assert "name" in b
        assert "path" in b
        assert "created_at" in b
        assert "image_count" in b
        assert b["image_count"] == 1


def test_save_skips_none_annotated(tmp_path):
    """save_batch handles images with annotated_rgb=None without crashing."""
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    images = _make_images(with_annotated=False)
    batch_dir = BatchManager.save_batch("no-annotated", images, PARAMS)
    assert batch_dir.exists()
    with open(batch_dir / "manifest.json", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["images"][0]["annotated_filename"] is None, \
        "annotated_filename should be null for unanalyzed images"


def test_save_converts_rgb_to_bgr(tmp_path):
    """save_batch saves annotated images in BGR format (cv2.imwrite expects BGR)."""
    import cv2
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    # Create a distinctive RGB image: R=255, G=0, B=0 (pure red in RGB)
    annotated_rgb = np.zeros((50, 50, 3), dtype=np.uint8)
    annotated_rgb[:, :, 0] = 255  # R channel in RGB
    images = {
        "img1.png": {
            "original_bgr": np.zeros((50, 50, 3), dtype=np.uint8),
            "original_rgb": np.zeros((50, 50, 3), dtype=np.uint8),
            "annotated_rgb": annotated_rgb,
            "algo_count": 5,
            "manual_marks": [],
        }
    }
    batch_dir = BatchManager.save_batch("bgr-test", images, PARAMS)
    # Read back the saved annotated image with cv2 (returns BGR)
    saved_bgr = cv2.imread(str(batch_dir / "annotated_img1.png"))
    assert saved_bgr is not None, "annotated image should exist on disk"
    # RGB R=255 -> after RGB2BGR conversion -> BGR R channel (index 2) = 255
    # cv2.imread returns BGR; BGR[0]=B, BGR[1]=G, BGR[2]=R
    # If correctly converted RGB->BGR, R value (255) is in BGR channel 2
    assert saved_bgr[0, 0, 2] == 255, "red channel in BGR should be 255 (was R=255 in RGB)"
    assert saved_bgr[0, 0, 0] == 0, "blue channel in BGR should be 0"


# ---- New tests for add_images, remove_image, update_manifest, export_csv ----

def _make_two_images(with_annotated=True):
    """Build a minimal _images dict with two images."""
    original_bgr = np.zeros((50, 50, 3), dtype=np.uint8)
    original_rgb = np.zeros((50, 50, 3), dtype=np.uint8)
    annotated_rgb = np.zeros((50, 50, 3), dtype=np.uint8) if with_annotated else None
    return {
        "img1.png": {
            "original_bgr": original_bgr,
            "original_rgb": original_rgb,
            "annotated_rgb": annotated_rgb,
            "algo_count": 5,
            "manual_marks": [(10, 20)],
        },
        "img2.png": {
            "original_bgr": original_bgr,
            "original_rgb": original_rgb,
            "annotated_rgb": annotated_rgb,
            "algo_count": 3,
            "manual_marks": [],
        },
    }


def test_add_images(tmp_path):
    """BMGR-04: add_images copies new files into batch folder and updates manifest images list."""
    import cv2
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    images = _make_images()
    batch_dir = BatchManager.save_batch("test-add", images, PARAMS)
    # Create a new image file to add
    new_img_path = tmp_path / "new_img.png"
    cv2.imwrite(str(new_img_path), np.zeros((50, 50, 3), dtype=np.uint8))
    added = BatchManager.add_images(batch_dir, [new_img_path])
    assert "new_img.png" in added, "should return added filename"
    manifest = BatchManager.load_batch(batch_dir)
    filenames = [img["filename"] for img in manifest["images"]]
    assert "new_img.png" in filenames, "new image should appear in manifest"
    assert (batch_dir / "new_img.png").exists(), "new image file should be copied to batch folder"


def test_add_images_no_duplicate(tmp_path):
    """BMGR-04: adding an image with same filename as existing one gets a suffix."""
    import cv2
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    images = _make_images()
    batch_dir = BatchManager.save_batch("test-dup", images, PARAMS)
    # Add a new image with the same filename as existing img1.png
    dup_path = tmp_path / "img1.png"
    cv2.imwrite(str(dup_path), np.zeros((50, 50, 3), dtype=np.uint8))
    added = BatchManager.add_images(batch_dir, [dup_path])
    assert len(added) == 1
    # Should not be "img1.png" (duplicate)
    assert added[0] != "img1.png", "duplicate filename should get a suffix"
    assert added[0].startswith("img1_"), f"suffixed name should start with 'img1_', got {added[0]}"
    manifest = BatchManager.load_batch(batch_dir)
    filenames = [img["filename"] for img in manifest["images"]]
    assert added[0] in filenames, "renamed file should appear in manifest"


def test_remove_image_no_delete(tmp_path):
    """BMGR-05: remove_image removes entry from manifest but file still exists on disk."""
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    images = _make_two_images()
    batch_dir = BatchManager.save_batch("test-remove", images, PARAMS)
    result = BatchManager.remove_image(batch_dir, "img2.png")
    assert result is True, "remove_image should return True when image found"
    manifest = BatchManager.load_batch(batch_dir)
    filenames = [img["filename"] for img in manifest["images"]]
    assert "img2.png" not in filenames, "img2.png should be removed from manifest"
    assert "img1.png" in filenames, "img1.png should still be in manifest"
    assert (batch_dir / "img2.png").exists(), "img2.png file should still exist on disk"


def test_remove_image_not_found(tmp_path):
    """BMGR-05: removing a filename not in manifest returns False (no error)."""
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    images = _make_images()
    batch_dir = BatchManager.save_batch("test-remove-nf", images, PARAMS)
    result = BatchManager.remove_image(batch_dir, "nonexistent.png")
    assert result is False, "remove_image should return False when image not found"


def test_update_manifest(tmp_path):
    """update_manifest rewrites manifest with new params and image data."""
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    images = _make_images()
    batch_dir = BatchManager.save_batch("test-update", images, PARAMS)
    # Update with new params and new count
    new_params = dict(PARAMS)
    new_params["brightness_threshold"] = 150
    updated_images = {
        "img1.png": {
            "original_bgr": np.zeros((50, 50, 3), dtype=np.uint8),
            "original_rgb": np.zeros((50, 50, 3), dtype=np.uint8),
            "annotated_rgb": np.zeros((50, 50, 3), dtype=np.uint8),
            "algo_count": 8,
            "manual_marks": [(5, 10)],
        }
    }
    BatchManager.update_manifest(batch_dir, updated_images, new_params)
    manifest = BatchManager.load_batch(batch_dir)
    assert manifest["parameters"]["brightness_threshold"] == 150
    assert manifest["images"][0]["cell_count"] == 8


def test_export_csv_columns(tmp_path):
    """BMGR-07: export_csv creates CSV with columns: filename, total_count, algo_count, manual_count."""
    import pandas as pd
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    images = _make_images(manual_marks=[(10, 20), (30, 40)])
    batch_dir = BatchManager.save_batch("test-export", images, PARAMS)
    output = tmp_path / "results.csv"
    manifest = BatchManager.load_batch(batch_dir)
    BatchManager.export_csv(manifest, output)
    df = pd.read_csv(output)
    assert list(df.columns) == ["filename", "total_count", "algo_count", "manual_count"], \
        f"unexpected columns: {list(df.columns)}"


def test_export_csv_row_count(tmp_path):
    """BMGR-07: export_csv has one row per image in manifest."""
    import pandas as pd
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    images = _make_two_images()
    batch_dir = BatchManager.save_batch("test-export-rows", images, PARAMS)
    output = tmp_path / "results.csv"
    manifest = BatchManager.load_batch(batch_dir)
    BatchManager.export_csv(manifest, output)
    df = pd.read_csv(output)
    assert len(df) == 2, f"expected 2 rows, got {len(df)}"


def test_export_csv_counts(tmp_path):
    """BMGR-07: manual_count = len(manual_marks), total = algo + manual."""
    import pandas as pd
    from batch_manager import BatchManager
    BatchManager.BATCHES_ROOT = tmp_path / "batches"
    marks = [(10, 20), (30, 40)]
    images = _make_images(manual_marks=marks)
    # algo_count is 5 (from _make_images), manual is 2
    batch_dir = BatchManager.save_batch("test-counts", images, PARAMS)
    output = tmp_path / "results.csv"
    manifest = BatchManager.load_batch(batch_dir)
    BatchManager.export_csv(manifest, output)
    df = pd.read_csv(output)
    row = df.iloc[0]
    assert row["algo_count"] == 5, f"algo_count should be 5, got {row['algo_count']}"
    assert row["manual_count"] == 2, f"manual_count should be 2, got {row['manual_count']}"
    assert row["total_count"] == 7, f"total_count should be 7, got {row['total_count']}"
