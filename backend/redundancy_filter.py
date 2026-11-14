"""
redundancy_filter.py — Mean Absolute Difference Redundancy Reduction for GeoForge

Eliminates near-duplicate consecutive drone frames while enforcing a safety
retention floor (keeping at least 50% of frames) to ensure baseline coverage
for Structure-from-Motion (SfM).
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict

import cv2
import numpy as np

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


# ============================================================
# CONFIGURATION
# ============================================================

# Minimum mean absolute pixel difference between consecutive
# frames for a frame to be considered non-redundant.
DEFAULT_DIFFERENCE_THRESHOLD = 5.0

# Safety floor: never remove more than this fraction of frames.
# Ensures continuous visual baseline for drone trajectories.
MAX_REMOVAL_RATIO = 0.50


def calculate_difference(image1: np.ndarray, image2: np.ndarray) -> float:
    """Calculate visual difference between two images using mean absolute difference (MAD)."""
    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    if gray1.shape != gray2.shape:
        gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))

    return float(cv2.absdiff(gray1, gray2).mean())


def remove_redundant_frames(
    input_dir: str,
    output_dir: str,
    difference_threshold: float = DEFAULT_DIFFERENCE_THRESHOLD,
    max_removal_ratio: float = MAX_REMOVAL_RATIO
) -> Dict[str, Any]:
    """
    Remove frames that are too similar to the previously selected keyframe.

    Preserves camera baseline while pruning static hover frames.
    Enforces safety floor to guarantee at least (1 - max_removal_ratio) frames are kept.
    Generates redundancy_summary.json with per-frame metrics.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    frames = sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not frames:
        raise RuntimeError(
            f"No image frames found in: {input_dir}\n"
            f"Supported extensions: {', '.join(IMAGE_EXTENSIONS)}"
        )

    logger.info(f"Redundancy filter input: {len(frames)} frames")
    logger.info(f"Difference threshold: {difference_threshold}")
    logger.info(f"Safety floor: keep at least {1.0 - max_removal_ratio:.0%} of frames")

    # Pass 1: compute differences between consecutive frames
    differences = []
    previous_image = None

    for frame_path in frames:
        image = cv2.imread(str(frame_path))
        if image is None:
            differences.append(None)
            continue

        if previous_image is None:
            differences.append(None)  # First frame has no predecessor
            previous_image = image
            continue

        diff = calculate_difference(previous_image, image)
        differences.append(diff)
        previous_image = image

    valid_diffs = [d for d in differences if d is not None]
    avg_diff = float(np.mean(valid_diffs)) if valid_diffs else 0.0
    min_diff = float(np.min(valid_diffs)) if valid_diffs else 0.0
    max_diff = float(np.max(valid_diffs)) if valid_diffs else 0.0

    logger.info(f"Frame differences: avg={avg_diff:.2f}, min={min_diff:.2f}, max={max_diff:.2f}")

    # Safety floor calculation
    would_remove = sum(1 for d in valid_diffs if d < difference_threshold)
    max_removable = int(len(frames) * max_removal_ratio)
    effective_threshold = difference_threshold

    if would_remove > max_removable and valid_diffs:
        sorted_diffs = sorted(valid_diffs)
        cutoff_index = min(max_removable, len(sorted_diffs) - 1)
        effective_threshold = sorted_diffs[cutoff_index] if cutoff_index >= 0 else 0.0
        logger.info(
            f"Safety floor engaged: threshold {difference_threshold} → {effective_threshold:.2f} "
            f"(would have removed {would_remove}/{len(frames)} frames)"
        )

    # Pass 2: filter frames and record results
    previous_image = None
    kept = 0
    removed = 0
    frame_actions = []

    for i, frame_path in enumerate(frames):
        image = cv2.imread(str(frame_path))
        if image is None:
            logger.warning(f"Could not read frame, skipping: {frame_path.name}")
            continue

        # Always keep the first frame
        if previous_image is None:
            shutil.copy2(frame_path, output_dir / frame_path.name)
            previous_image = image
            kept += 1
            frame_actions.append({
                "filename": frame_path.name,
                "action": "kept",
                "reason": "first_frame",
                "difference": 0.0
            })
            continue

        diff = calculate_difference(previous_image, image)
        if diff >= effective_threshold:
            shutil.copy2(frame_path, output_dir / frame_path.name)
            previous_image = image
            kept += 1
            frame_actions.append({
                "filename": frame_path.name,
                "action": "kept",
                "reason": "significant_motion",
                "difference": round(diff, 2)
            })
        else:
            removed += 1
            frame_actions.append({
                "filename": frame_path.name,
                "action": "removed",
                "reason": "redundant_near_duplicate",
                "difference": round(diff, 2)
            })

    logger.info(f"Redundancy filtering complete: {kept}/{len(frames)} frames kept ({removed} redundant removed)")

    summary_manifest = {
        "input_frames": len(frames),
        "frames_kept": kept,
        "frames_removed": removed,
        "thresholds": {
            "effective_difference": effective_threshold,
            "baseline_difference": difference_threshold,
            "max_removal_ratio": max_removal_ratio
        },
        "metrics": {
            "avg_difference": round(avg_diff, 2),
            "min_difference": round(min_diff, 2),
            "max_difference": round(max_diff, 2)
        },
        "frames": frame_actions
    }
    # Save summary in the parent job directory so COLMAP image scanner does not parse it
    summary_path = output_dir.parent / "redundancy_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_manifest, f, indent=2)

    return {
        "input_frames": len(frames),
        "frames_kept": kept,
        "redundant_frames_removed": removed,
        "difference_threshold": effective_threshold,
        "original_threshold": difference_threshold,
        "summary_file": str(summary_path)
    }
