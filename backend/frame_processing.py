import logging
import cv2
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

# Target frames per second to extract from the video.
# For drone video, 2-3 fps provides good baseline coverage.
# This is used to calculate the frame interval dynamically
# based on the video's actual FPS, instead of a fixed skip.
DEFAULT_TARGET_FPS = 2.0

# JPEG quality for extracted frames (0-100).
# Higher values preserve detail for SIFT feature extraction.
JPEG_QUALITY = 95


def extract_frames(
    video_path: str,
    output_dir: str,
    interval: int = None,
    target_fps: float = DEFAULT_TARGET_FPS
):
    """
    Extract frames from a video.

    If `interval` is provided, use it directly (legacy behaviour).
    Otherwise, calculate interval from video FPS and target_fps
    so that approximately `target_fps` frames per second are extracted,
    regardless of whether the source is 24fps, 30fps, or 60fps.
    """

    video_path = Path(video_path)
    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_seconds = total_frames / fps if fps > 0 else 0

    logger.info(f"Video metadata:")
    logger.info(f"  Path       : {video_path}")
    logger.info(f"  Resolution : {width} x {height}")
    logger.info(f"  FPS        : {fps:.2f}")
    logger.info(f"  Total frames: {total_frames}")
    logger.info(f"  Duration   : {duration_seconds:.1f} seconds")

    # --------------------------------------------------------
    # Calculate frame interval
    # --------------------------------------------------------

    if interval is not None:
        # Legacy mode: use the provided fixed interval
        effective_interval = max(1, interval)
        logger.info(f"  Frame interval: {effective_interval} (fixed)")
    else:
        # FPS-aware mode: calculate from target_fps
        if fps > 0 and target_fps > 0:
            effective_interval = max(1, int(round(fps / target_fps)))
        else:
            effective_interval = 5  # safe fallback
        logger.info(f"  Target FPS : {target_fps}")
        logger.info(f"  Frame interval: {effective_interval} (calculated from {fps:.1f} fps / {target_fps} target)")

    estimated_output = total_frames // effective_interval if effective_interval > 0 else total_frames
    logger.info(f"  Estimated output frames: ~{estimated_output}")

    # --------------------------------------------------------
    # Extract frames
    # --------------------------------------------------------

    frame_number = 0
    saved_frames = 0

    # JPEG compression parameters for higher quality
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]

    while True:
        success, frame = cap.read()

        if not success:
            break

        if frame_number % effective_interval == 0:
            output_file = output_dir / f"frame_{saved_frames:06d}.jpg"
            cv2.imwrite(str(output_file), frame, encode_params)
            saved_frames += 1

        frame_number += 1

    cap.release()

    logger.info(f"Frames extracted: {saved_frames}")
    logger.info(f"JPEG quality: {JPEG_QUALITY}")

    return {
        "total_frames": total_frames,
        "fps": fps,
        "width": width,
        "height": height,
        "duration_seconds": round(duration_seconds, 1),
        "frame_interval": effective_interval,
        "frames_saved": saved_frames,
        "output_directory": str(output_dir)
    }