import logging
import shutil
import cv2
import numpy as np
from pathlib import Path

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
# the threshold is automatically lowered to keep enough frames.
# This prevents the pipeline from discarding most of the video
# when it was shot in slightly soft conditions.
MAX_BLUR_REJECTION_RATIO = 0.40

# Absolute minimum sharpness — frames below this are almost
# certainly motion-blurred beyond usefulness.
ABSOLUTE_MIN_SHARPNESS = 20.0

# Brightness bounds (0-255 grayscale mean).
# Frames outside this range are poorly exposed.
MIN_BRIGHTNESS = 30.0
MAX_BRIGHTNESS = 240.0


def calculate_sharpness(image_path: Path) -> float:
    """
    Calculate image sharpness using Laplacian variance.
    Higher value = sharper image.
    """

    image = cv2.imread(str(image_path))

    if image is None:
        return 0.0

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    return cv2.Laplacian(gray, cv2.CV_64F).var()


def calculate_brightness(image_path: Path) -> float:
    """
    Calculate mean brightness of an image.
    Returns the mean intensity of the grayscale image (0-255).
    """

    image = cv2.imread(str(image_path))

    if image is None:
        return 0.0

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    return float(gray.mean())


def filter_sharp_frames(
    frames_dir: str,
    selected_dir: str,
    threshold: float = DEFAULT_SHARPNESS_THRESHOLD,
    min_brightness: float = MIN_BRIGHTNESS,
    max_brightness: float = MAX_BRIGHTNESS
):
    """
    Remove blurry and poorly exposed frames based on sharpness
    and brightness.

    Frames with sharpness >= threshold AND brightness within
    [min_brightness, max_brightness] are kept.

    If too many frames would be rejected (>MAX_BLUR_REJECTION_RATIO),
    the threshold is adaptively lowered to keep enough frames.

    Accepts .jpg, .jpeg, and .png files.
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

    logger.info(f"Frames found: {len(frame_files)}")
    logger.info(f"Sharpness threshold: {threshold}")
    logger.info(f"Brightness range: [{min_brightness}, {max_brightness}]")
    logger.info("Analyzing frames...")

    # --------------------------------------------------------
    # First pass: compute scores for all frames
    # --------------------------------------------------------

    frame_scores = []

    for frame in frame_files:
        sharpness = calculate_sharpness(frame)
        brightness = calculate_brightness(frame)
        frame_scores.append({
            "path": frame,
            "sharpness": sharpness,
            "brightness": brightness,
        })

    all_sharpness = [s["sharpness"] for s in frame_scores]
    avg_sharpness = sum(all_sharpness) / len(all_sharpness) if all_sharpness else 0.0
    median_sharpness = float(np.median(all_sharpness)) if all_sharpness else 0.0

    logger.info(f"Average sharpness : {avg_sharpness:.1f}")
    logger.info(f"Median sharpness  : {median_sharpness:.1f}")
    logger.info(f"Min sharpness     : {min(all_sharpness):.1f}")
    logger.info(f"Max sharpness     : {max(all_sharpness):.1f}")

    # --------------------------------------------------------
    # Adaptive threshold
    # --------------------------------------------------------
    # If the fixed threshold would reject too many frames,
    # lower it to keep at least (1 - MAX_BLUR_REJECTION_RATIO)
    # of the frames. This handles videos shot in slightly
    # soft conditions (e.g., haze, gentle motion) without
    # losing the entire dataset.

    effective_threshold = threshold

    passing_count = sum(1 for s in all_sharpness if s >= threshold)
    rejection_ratio = 1.0 - (passing_count / len(all_sharpness)) if all_sharpness else 0.0

    if rejection_ratio > MAX_BLUR_REJECTION_RATIO:
        # Use a percentile-based threshold: keep at least 60% of frames
        keep_fraction = 1.0 - MAX_BLUR_REJECTION_RATIO
        sorted_sharpness = sorted(all_sharpness)
        percentile_index = max(0, int(len(sorted_sharpness) * (1.0 - keep_fraction)) - 1)
        adaptive_threshold = sorted_sharpness[percentile_index]

        # Don't go below absolute minimum
        effective_threshold = max(adaptive_threshold, ABSOLUTE_MIN_SHARPNESS)

        logger.info(
            f"Adaptive threshold engaged: {threshold} → {effective_threshold:.1f} "
            f"(original would reject {rejection_ratio:.0%} of frames)"
        )

    # --------------------------------------------------------
    # Second pass: filter frames
    # --------------------------------------------------------

    kept = 0
    removed_blur = 0
    removed_brightness = 0
    scores = []

    for entry in frame_scores:
        frame = entry["path"]
        sharpness = entry["sharpness"]
        brightness = entry["brightness"]

        scores.append(sharpness)

        # Check brightness first
        if brightness < min_brightness or brightness > max_brightness:
            removed_brightness += 1
            logger.debug(f"  {frame.name}: REJECTED brightness={brightness:.1f}")
            continue

        # Check sharpness
        if sharpness >= effective_threshold:
            shutil.copy2(frame, selected_dir / frame.name)
            kept += 1
        else:
            removed_blur += 1
            logger.debug(f"  {frame.name}: REJECTED sharpness={sharpness:.1f}")

    logger.info(f"Effective sharpness threshold: {effective_threshold}")
    logger.info(f"Frames kept                 : {kept}")
    logger.info(f"Rejected for blur           : {removed_blur}")
    logger.info(f"Rejected for brightness     : {removed_brightness}")

    return {
        "total_frames": len(frame_files),
        "frames_kept": kept,
        "blurry_frames_removed": removed_blur,
        "brightness_frames_removed": removed_brightness,
        "threshold": effective_threshold,
        "original_threshold": threshold,
        "avg_sharpness": round(avg_sharpness, 1),
        "median_sharpness": round(median_sharpness, 1)
    }