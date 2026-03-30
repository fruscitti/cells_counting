"""BatchManager — pure Python batch persistence module. No Qt imports."""
import json
import os
import shutil
import tempfile
import cv2
from datetime import datetime, timezone
from pathlib import Path


class BatchManager:
    """Manages saving, loading, and listing analysis batches.

    A batch is a folder under BATCHES_ROOT with:
    - manifest.json: metadata, parameters, image list with marks and counts
    - <filename>: copy of each original image
    - annotated_<filename>: annotated image (if analysis was run)
    """

    SCHEMA_VERSION = 1
    BATCHES_ROOT = Path(__file__).parent / "batches"

    @classmethod
    def save_batch(cls, name: str, images: dict, params: dict) -> Path:
        """Save a named batch. Returns the batch directory path.

        Args:
            name: human-readable batch name (used in folder name)
            images: _images dict from MainWindow — {filename: {"original_bgr", "original_rgb",
                    "annotated_rgb", "algo_count", "manual_marks"}}
            params: parameter dict from ParamPanel.get_params()

        Returns:
            Path to the created batch directory.
        """
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        folder_name = f"{date_str}_{name}"
        batch_dir = cls._resolve_unique(cls.BATCHES_ROOT / folder_name)
        batch_dir.mkdir(parents=True)

        manifest_images = []
        for filename, entry in images.items():
            # Save original image (original_bgr is already in BGR for cv2.imwrite)
            orig_dest = batch_dir / filename
            cv2.imwrite(str(orig_dest), entry["original_bgr"])

            # Save annotated if it exists (annotated_rgb is RGB, must convert to BGR)
            annotated_fn = None
            if entry.get("annotated_rgb") is not None:
                annotated_fn = f"annotated_{filename}"
                # Pitfall 1 from RESEARCH: cv2.imwrite expects BGR, _images stores RGB
                bgr = cv2.cvtColor(entry["annotated_rgb"], cv2.COLOR_RGB2BGR)
                cv2.imwrite(str(batch_dir / annotated_fn), bgr)

            removed = set(entry.get("removed_indices", []))
            active_algo = len(entry.get("algo_centroids", [])) - len(removed)
            manifest_images.append({
                "filename": filename,
                "original_filename": filename,
                "annotated_filename": annotated_fn,
                "cell_count": active_algo + len(entry.get("manual_marks", [])),
                "manual_marks": [list(m) for m in entry.get("manual_marks", [])],
                "algo_centroids": [list(c) for c in entry.get("algo_centroids", [])],
                "removed_indices": list(entry.get("removed_indices", [])),
                "analyzed_at": (
                    datetime.now(timezone.utc).isoformat()
                    if entry.get("annotated_rgb") is not None
                    else None
                ),
            })

        manifest = {
            "schema_version": cls.SCHEMA_VERSION,
            "name": name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "modified_at": datetime.now(timezone.utc).isoformat(),
            "parameters": dict(params),
            "images": manifest_images,
        }
        cls._atomic_write_manifest(batch_dir, manifest)
        return batch_dir

    @classmethod
    def load_batch(cls, batch_dir: Path) -> dict:
        """Load manifest from batch_dir and compute status for each image.

        Status 'ok' means the original file exists on disk.
        Status 'missing' means the file has been moved or deleted.
        manual_marks are converted from JSON lists to tuples on load.

        Returns:
            manifest dict with computed 'status' field per image entry.
        """
        with open(batch_dir / "manifest.json", encoding="utf-8") as f:
            manifest = json.load(f)
        for img_entry in manifest["images"]:
            img_path = batch_dir / img_entry["filename"]
            img_entry["status"] = "ok" if img_path.exists() else "missing"
            # Pitfall 2 from RESEARCH: JSON tuples round-trip as lists; normalize to tuples
            img_entry["manual_marks"] = [
                tuple(m) for m in img_entry.get("manual_marks", [])
            ]
            img_entry["algo_centroids"] = [tuple(c) for c in img_entry.get("algo_centroids", [])]
            img_entry["removed_indices"] = list(img_entry.get("removed_indices", []))
        return manifest

    @classmethod
    def list_batches(cls) -> list:
        """Return sorted list of batch metadata dicts (newest first).

        Each dict has: name, path, created_at, image_count.
        Folders without manifest.json are silently skipped.
        """
        if not cls.BATCHES_ROOT.exists():
            return []
        batches = []
        for d in sorted(cls.BATCHES_ROOT.iterdir(), reverse=True):
            manifest_path = d / "manifest.json"
            if d.is_dir() and manifest_path.exists():
                with open(manifest_path, encoding="utf-8") as f:
                    m = json.load(f)
                batches.append({
                    "name": m["name"],
                    "path": d,
                    "created_at": m["created_at"],
                    "image_count": len(m["images"]),
                })
        return batches

    @classmethod
    def _atomic_write_manifest(cls, batch_dir: Path, manifest: dict):
        """Write manifest atomically using tempfile + os.replace.

        Guarantees that a crash mid-write cannot leave a corrupt manifest.json.
        The temp file is created in the same directory to ensure same filesystem
        (required for atomic os.replace on POSIX).
        """
        target = batch_dir / "manifest.json"
        fd, tmp_path = tempfile.mkstemp(dir=str(batch_dir), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            os.replace(tmp_path, str(target))
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    @classmethod
    def add_images(cls, batch_dir: Path, image_paths: list) -> list:
        """Copy new images into batch folder, update manifest. Returns list of added filenames."""
        manifest = cls.load_batch(batch_dir)
        existing_filenames = {img["filename"] for img in manifest["images"]}
        added = []
        for src in image_paths:
            src = Path(src)
            dest_name = src.name
            # Handle duplicate filenames
            if dest_name in existing_filenames:
                stem, suffix = src.stem, src.suffix
                counter = 2
                while f"{stem}_{counter}{suffix}" in existing_filenames:
                    counter += 1
                dest_name = f"{stem}_{counter}{suffix}"
            shutil.copy2(str(src), str(batch_dir / dest_name))
            manifest["images"].append({
                "filename": dest_name,
                "original_filename": src.name,
                "annotated_filename": None,
                "cell_count": 0,
                "manual_marks": [],
                "analyzed_at": None,
            })
            existing_filenames.add(dest_name)
            added.append(dest_name)
        manifest["modified_at"] = datetime.now(timezone.utc).isoformat()
        # Remove computed "status" fields before writing
        for img in manifest["images"]:
            img.pop("status", None)
        cls._atomic_write_manifest(batch_dir, manifest)
        return added

    @classmethod
    def remove_image(cls, batch_dir: Path, filename: str) -> bool:
        """Remove image entry from manifest. Does NOT delete file from disk. Returns True if found."""
        manifest = cls.load_batch(batch_dir)
        original_len = len(manifest["images"])
        manifest["images"] = [img for img in manifest["images"] if img["filename"] != filename]
        if len(manifest["images"]) == original_len:
            return False
        manifest["modified_at"] = datetime.now(timezone.utc).isoformat()
        for img in manifest["images"]:
            img.pop("status", None)
        cls._atomic_write_manifest(batch_dir, manifest)
        return True

    @classmethod
    def update_manifest(cls, batch_dir: Path, images: dict, params: dict):
        """Rewrite manifest with current image data and parameters (after re-analyze)."""
        manifest = cls.load_batch(batch_dir)
        manifest["parameters"] = dict(params)
        manifest["modified_at"] = datetime.now(timezone.utc).isoformat()
        for img_entry in manifest["images"]:
            fn = img_entry["filename"]
            if fn in images:
                entry = images[fn]
                removed = set(entry.get("removed_indices", []))
                active_algo = len(entry.get("algo_centroids", [])) - len(removed)
                img_entry["cell_count"] = active_algo + len(entry.get("manual_marks", []))
                img_entry["manual_marks"] = [list(m) for m in entry.get("manual_marks", [])]
                img_entry["algo_centroids"] = [list(c) for c in entry.get("algo_centroids", [])]
                img_entry["removed_indices"] = list(entry.get("removed_indices", []))
                img_entry["analyzed_at"] = datetime.now(timezone.utc).isoformat()
                # Save updated annotated image if exists
                if entry.get("annotated_rgb") is not None:
                    annotated_fn = f"annotated_{fn}"
                    bgr = cv2.cvtColor(entry["annotated_rgb"], cv2.COLOR_RGB2BGR)
                    cv2.imwrite(str(batch_dir / annotated_fn), bgr)
                    img_entry["annotated_filename"] = annotated_fn
            img_entry.pop("status", None)
        cls._atomic_write_manifest(batch_dir, manifest)

    @classmethod
    def export_csv(cls, manifest: dict, output_path: Path):
        """Export batch results to CSV with filename, total_count, algo_count, manual_count."""
        import pandas as pd
        rows = []
        for img in manifest["images"]:
            algo = img.get("cell_count", 0) or 0
            manual = len(img.get("manual_marks", []))
            rows.append({
                "filename": img["original_filename"],
                "total_count": algo + manual,
                "algo_count": algo,
                "manual_count": manual,
            })
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)

    @classmethod
    def _resolve_unique(cls, candidate: Path) -> Path:
        """Return candidate path if it doesn't exist, otherwise append _2, _3, etc."""
        if not candidate.exists():
            return candidate
        base = str(candidate)
        counter = 2
        while True:
            p = Path(f"{base}_{counter}")
            if not p.exists():
                return p
            counter += 1
