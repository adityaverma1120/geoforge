import logging
import shutil
import cv2
from pathlib import Path

logger = logging.getLogger(__name__)

# Supported image extensions (must match frame_processing.py output)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


# ============================================================
# CONFIGURATION
# ============================================================

# Minimum mean absolute pixel difference between consecutive
# frames for a frame to be considered non-redundant.
# Lower = keep more similar frames (more data for COLMAP).
# For drone video, even similar frames provide useful
# camera baseline information.
DEFAULT_DIFFERENCE_THRESHOLD = 5.0

# Safety floor: never remove more than this fraction of frames.
# This prevents catastrophic data loss when the threshold is
# accidentally set too high or the video has consistent panning.
MAX_REMOVAL_RATIO = 0.50


def calculate_difference(image1, image2):
    """Calculate visual difference between two images using mean absolute difference."""

    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    # Resize to same dimensions if they differ
    if gray1.shape != gray2.shape:
        gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))

    return cv2.absdiff(gray1, gray2).mean()


def remove_redundant_frames(
    input_dir: str,
    output_dir: str,
    difference_threshold: float = DEFAULT_DIFFERENCE_THRESHOLD
):
    """
    Remove frames that are too similar to the previously selected frame.

    For drone video, consecutive frames often look similar but still
    provide useful camera-baseline information for stereo matching.
    The threshold is therefore kept relatively low.

    A safety floor prevents removing more than MAX_REMOVAL_RATIO
    of the total frames, even if many are below the threshold.

    Accepts .jpg, .jpeg, and .png files.
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
    logger.info(f"Safety floor: keep at least {1.0 - MAX_REMOVAL_RATIO:.0%} of frames")

    # --------------------------------------------------------
    # First pass: compute all differences to build statistics
    # --------------------------------------------------------

    differences = []
    previous_image = None

    for frame_path in frames:
        image = cv2.imread(str(frame_path))

        if image is None:
            differences.append(None)
            continue

        if previous_image is None:
            differences.append(None)  # first frame, no diff
            previous_image = image
            continue

        diff = calculate_difference(previous_image, image)
        differences.append(diff)
        previous_image = image

    valid_diffs = [d for d in differences if d is not None]
    if valid_diffs:
        avg_diff = sum(valid_diffs) / len(valid_diffs)
        min_diff = min(valid_diffs)
        max_diff = max(valid_diffs)
        logger.info(f"Frame differences: avg={avg_diff:.2f}, min={min_diff:.2f}, max={max_diff:.2f}")

    # --------------------------------------------------------
    # Determine how many would be removed with the threshold
    # --------------------------------------------------------

    would_remove = sum(1 for d in valid_diffs if d < difference_threshold)
    max_removable = int(len(frames) * MAX_REMOVAL_RATIO)

    effective_threshold = difference_threshold

    if would_remove > max_removable and valid_diffs:
        # Too many would be removed — lower the threshold
        sorted_diffs = sorted(valid_diffs)
        # Find the threshold that keeps at least (1 - MAX_REMOVAL_RATIO) fraction
        cutoff_index = min(max_removable, len(sorted_diffs) - 1)
        effective_threshold = sorted_diffs[cutoff_index] if cutoff_index >= 0 else 0.0
        logger.info(
            f"Safety floor engaged: threshold {difference_threshold} → {effective_threshold:.2f} "
            f"(would have removed {would_remove}/{len(frames)} frames)"
        )

    # --------------------------------------------------------
    # Second pass: actually filter frames
    # --------------------------------------------------------

    previous_image = None
    kept = 0
    removed = 0

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
            continue

        difference = calculate_difference(previous_image, image)

        if difference >= effective_threshold:
            shutil.copy2(frame_path, output_dir / frame_path.name)
            previous_image = image
            kept += 1
        else:
            removed += 1

    logger.info(f"Effective threshold : {effective_threshold:.2f}")
    logger.info(f"Frames kept         : {kept}")
    logger.info(f"Frames removed      : {removed}")

    return {
        "input_frames": len(frames),
        "frames_kept": kept,
        "redundant_frames_removed": removed,
        "difference_threshold": effective_threshold,
        "original_threshold": difference_threshold
    }