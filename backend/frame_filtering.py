"""
frame_filtering.py — Image Quality, Sharpness & Exposure Filtering for GeoForge

Evaluates:
1. Sharpness via Laplacian variance.
2. Exposure / Brightness via mean grayscale intensity.
3. Contrast via standard deviation of luminance.
4. Adaptive thresholding to prevent excessive frame rejection.
5. Generates detailed filtering_summary.json with rejection reasons.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Supported image extensions (must match frame_processing.py output)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


# ============================================================
# CONFIGURATION
# ============================================================

# Default Laplacian variance threshold for sharpness.
# Frames below this are considered blurry.
DEFAULT_SHARPNESS_THRESHOLD = 100.0

# If more than this fraction of frames are rejected as blurry,
# the threshold is adaptively lowered to avoid starving the SfM pipeline.
MAX_BLUR_REJECTION_RATIO = 0.40

# Absolute minimum sharpness floor — frames below this are motion-blurred beyond utility.
ABSOLUTE_MIN_SHARPNESS = 20.0

# Brightness bounds (0-255 grayscale mean intensity).
MIN_BRIGHTNESS = 30.0
MAX_BRIGHTNESS = 240.0

# Minimum contrast threshold (grayscale pixel standard deviation).
# Frames with std < 15.0 lack visual gradients/features needed by SIFT.
MIN_CONTRAST = 15.0


def calculate_sharpness(image_path: Path) -> float:
    """
    Calculate image sharpness using Laplacian variance.
    Higher value = sharper image with higher frequency content.
    """
    image = cv2.imread(str(image_path))
    if image is None:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def calculate_brightness(image_path: Path) -> float:
    """
    Calculate mean luminance intensity of an image (0-255).
    """
    image = cv2.imread(str(image_path))
    if image is None:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(gray.mean())


def calculate_contrast(image_path: Path) -> float:
    """
    Calculate image contrast via standard deviation of grayscale intensities.
    Higher value = richer dynamic range for feature detection.
    """
    image = cv2.imread(str(image_path))
    if image is None:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(gray.std())


def filter_sharp_frames(
    frames_dir: str,
    selected_dir: str,
    threshold: float = DEFAULT_SHARPNESS_THRESHOLD,
    min_brightness: float = MIN_BRIGHTNESS,
    max_brightness: float = MAX_BRIGHTNESS,
    min_contrast: float = MIN_CONTRAST
) -> Dict[str, Any]:
    """
    Filter extracted frames by sharpness, exposure, and contrast.

    Rejection criteria:
        1. Brightness out of bounds ([min_brightness, max_brightness]).
        2. Contrast below min_contrast.
        3. Sharpness below effective threshold (with adaptive relaxation).

    Records:
        - Total extracted frames
        - Accepted frames
        - Rejected frames
        - Breakdown of rejection reasons
        - Generates filtering_summary.json
    """
    frames_dir = Path(frames_dir)
    selected_dir = Path(selected_dir)
    selected_dir.mkdir(parents=True, exist_ok=True)

    frame_files = sorted(
        p for p in frames_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not frame_files:
        raise RuntimeError(
            f"No image frames found in: {frames_dir}\n"
            f"Supported extensions: {', '.join(IMAGE_EXTENSIONS)}"
        )

    logger.info(f"Filtering {len(frame_files)} candidate frames:")
    logger.info(f"  Sharpness baseline : {threshold}")
    logger.info(f"  Brightness range   : [{min_brightness}, {max_brightness}]")
    logger.info(f"  Minimum contrast   : {min_contrast}")

    # Pass 1: compute metrics across all frames
    frame_scores = []
    for frame in frame_files:
        sharpness = calculate_sharpness(frame)
        brightness = calculate_brightness(frame)
        contrast = calculate_contrast(frame)
        frame_scores.append({
            "path": frame,
            "filename": frame.name,
            "sharpness": sharpness,
            "brightness": brightness,
            "contrast": contrast
        })

    all_sharpness = [s["sharpness"] for s in frame_scores]
    all_brightness = [s["brightness"] for s in frame_scores]
    all_contrast = [s["contrast"] for s in frame_scores]

    avg_sharpness = float(np.mean(all_sharpness)) if all_sharpness else 0.0
    median_sharpness = float(np.median(all_sharpness)) if all_sharpness else 0.0
    avg_brightness = float(np.mean(all_brightness)) if all_brightness else 0.0
    avg_contrast = float(np.mean(all_contrast)) if all_contrast else 0.0

    logger.info(f"Frame analysis: Avg sharpness={avg_sharpness:.1f}, Avg brightness={avg_brightness:.1f}, Avg contrast={avg_contrast:.1f}")

    # Adaptive sharpness thresholding:
    # If the fixed threshold would reject > MAX_BLUR_REJECTION_RATIO, adaptively lower it
    effective_threshold = threshold
    passing_count = sum(1 for s in all_sharpness if s >= threshold)
    rejection_ratio = 1.0 - (passing_count / len(all_sharpness)) if all_sharpness else 0.0

    if rejection_ratio > MAX_BLUR_REJECTION_RATIO:
        keep_fraction = 1.0 - MAX_BLUR_REJECTION_RATIO
        sorted_sharpness = sorted(all_sharpness)
        percentile_index = max(0, int(len(sorted_sharpness) * (1.0 - keep_fraction)) - 1)
        adaptive_threshold = sorted_sharpness[percentile_index]
        effective_threshold = max(adaptive_threshold, ABSOLUTE_MIN_SHARPNESS)
        logger.info(
            f"Adaptive sharpness engaged: {threshold} → {effective_threshold:.1f} "
            f"(would have rejected {rejection_ratio:.0%} of frames)"
        )

    # Pass 2: filter and record rejection reasons
    kept = 0
    rejected_blur = 0
    rejected_brightness = 0
    rejected_contrast = 0
    per_frame_results = []

    for entry in frame_scores:
        frame = entry["path"]
        sharpness = entry["sharpness"]
        brightness = entry["brightness"]
        contrast = entry["contrast"]

        rejection_reason = None

        if brightness < min_brightness:
            rejection_reason = f"underexposed (brightness {brightness:.1f} < {min_brightness})"
            rejected_brightness += 1
        elif brightness > max_brightness:
            rejection_reason = f"overexposed (brightness {brightness:.1f} > {max_brightness})"
            rejected_brightness += 1
        elif contrast < min_contrast:
            rejection_reason = f"low_contrast (contrast {contrast:.1f} < {min_contrast})"
            rejected_contrast += 1
        elif sharpness < effective_threshold:
            rejection_reason = f"motion_blur (sharpness {sharpness:.1f} < {effective_threshold:.1f})"
            rejected_blur += 1
        else:
            # Accepted
            shutil.copy2(frame, selected_dir / frame.name)
            kept += 1

        per_frame_results.append({
            "filename": frame.name,
            "accepted": rejection_reason is None,
            "rejection_reason": rejection_reason,
            "sharpness": round(sharpness, 1),
            "brightness": round(brightness, 1),
            "contrast": round(contrast, 1)
        })

    total_rejected = rejected_blur + rejected_brightness + rejected_contrast
    logger.info(
        f"Filtering complete: {kept}/{len(frame_files)} frames accepted "
        f"({total_rejected} rejected: {rejected_blur} blur, {rejected_brightness} exposure, {rejected_contrast} contrast)"
    )

    summary_data = {
        "total_frames": len(frame_files),
        "frames_kept": kept,
        "frames_rejected": total_rejected,
        "rejection_breakdown": {
            "blur": rejected_blur,
            "exposure": rejected_brightness,
            "contrast": rejected_contrast
        },
        "thresholds": {
            "effective_sharpness": effective_threshold,
            "baseline_sharpness": threshold,
            "min_brightness": min_brightness,
            "max_brightness": max_brightness,
            "min_contrast": min_contrast
        },
        "metrics": {
            "avg_sharpness": round(avg_sharpness, 1),
            "median_sharpness": round(median_sharpness, 1),
            "avg_brightness": round(avg_brightness, 1),
            "avg_contrast": round(avg_contrast, 1)
        },
        "frames": per_frame_results
    }

    summary_path = selected_dir / "filtering_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    return {
        "total_frames": len(frame_files),
        "frames_kept": kept,
        "blurry_frames_removed": rejected_blur,
        "brightness_frames_removed": rejected_brightness,
        "contrast_frames_removed": rejected_contrast,
        "threshold": effective_threshold,
        "original_threshold": threshold,
        "avg_sharpness": round(avg_sharpness, 1),
        "median_sharpness": round(median_sharpness, 1),
        "summary_file": str(summary_path)
    }
