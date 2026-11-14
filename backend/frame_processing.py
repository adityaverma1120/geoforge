"""
frame_processing.py — Video Ingestion, Validation & Intelligent Frame Extraction for GeoForge

Handles:
1. Video stream validation (integrity, decodability, duration, resolution, codec).
2. Intelligent, FPS-aware, resource-bounded frame extraction.
3. Metadata capture (per-frame timestamps, frame intervals).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import cv2

logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

# Target frames per second to extract from the video.
# For drone video, 2.0 fps provides optimal visual baseline and overlap.
DEFAULT_TARGET_FPS = 2.0

# Maximum frames to extract for single-job reconstruction.
# Bounded to protect 6 GB VRAM and 16 GB host RAM during COLMAP MVS and Open3D meshing.
MAX_EXTRACTED_FRAMES = 200

# Minimum acceptable video resolution for photogrammetric reconstruction.
MIN_VIDEO_WIDTH = 320
MIN_VIDEO_HEIGHT = 240

# Minimum and maximum acceptable duration in seconds.
MIN_DURATION_SECONDS = 1.0
MAX_DURATION_SECONDS = 1800.0  # 30 minutes

# JPEG quality for extracted frames (0-100). 95 preserves SIFT keypoint detail.
JPEG_QUALITY = 95


# ============================================================
# STAGE 1 — VIDEO VALIDATION
# ============================================================

def validate_video(video_path: Path) -> Dict[str, Any]:
    """
    Validate that an uploaded video is readable, structurally sound,
    and meets minimum photogrammetric reconstruction criteria.

    Extracts:
        - duration_seconds
        - fps
        - resolution (width, height)
        - total_frames
        - codec (FourCC)
        - file_size_bytes

    Raises:
        RuntimeError or ValueError on validation failure.
    """
    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    file_size = video_path.stat().st_size
    if file_size == 0:
        raise ValueError("Uploaded video file is 0 bytes (empty).")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(
            f"Could not open video file '{video_path.name}'. "
            "The container format or codec may be unsupported or corrupted."
        )

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))

        # Decode FourCC into ASCII string
        codec = "".join([chr((fourcc_int >> (8 * i)) & 0xFF) for i in range(4)]).strip()
        if not codec:
            codec = "UNKNOWN"

        duration_seconds = total_frames / fps if (fps > 0 and total_frames > 0) else 0.0

        # Validate visual dimensions
        if width <= 0 or height <= 0:
            raise ValueError(f"Video reports invalid visual dimensions: {width}x{height}.")

        if width < MIN_VIDEO_WIDTH or height < MIN_VIDEO_HEIGHT:
            raise ValueError(
                f"Video resolution ({width}x{height}) is below minimum required "
                f"({MIN_VIDEO_WIDTH}x{MIN_VIDEO_HEIGHT}) for photogrammetric reconstruction."
            )

        # Validate frame count
        if total_frames <= 0:
            raise ValueError("Video contains no readable frames (frame count is 0).")

        # Validate duration bounds
        if duration_seconds < MIN_DURATION_SECONDS:
            raise ValueError(
                f"Video duration ({duration_seconds:.2f}s) is too short. "
                f"Minimum required is {MIN_DURATION_SECONDS:.1f}s."
            )

        if duration_seconds > MAX_DURATION_SECONDS:
            raise ValueError(
                f"Video duration ({duration_seconds / 60:.1f} mins) exceeds maximum allowed "
                f"({MAX_DURATION_SECONDS / 60:.0f} mins)."
            )

        # Deep frame read check: probe first frame and middle frame to ensure stream is not truncated
        success, first_frame = cap.read()
        if not success or first_frame is None or first_frame.size == 0:
            raise ValueError("Failed to decode initial video frame. Video stream appears corrupted.")

        if total_frames > 10:
            mid_idx = total_frames // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_idx)
            success_mid, mid_frame = cap.read()
            if not success_mid or mid_frame is None:
                logger.warning(f"Warning: mid-point frame seek ({mid_idx}) returned empty. File may be partially truncated.")

        metadata = {
            "valid": True,
            "filename": video_path.name,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "width": width,
            "height": height,
            "resolution": f"{width}x{height}",
            "fps": round(fps, 2),
            "total_frames": total_frames,
            "duration_seconds": round(duration_seconds, 2),
            "codec": codec
        }

        logger.info(
            f"Video validation PASSED for '{video_path.name}': "
            f"{width}x{height} @ {fps:.2f} FPS | {total_frames} frames ({duration_seconds:.1f}s) | Codec: {codec}"
        )
        return metadata

    finally:
        cap.release()


# ============================================================
# STAGE 2 — INTELLIGENT FRAME EXTRACTION
# ============================================================

def extract_frames(
    video_path: str,
    output_dir: str,
    interval: Optional[int] = None,
    target_fps: float = DEFAULT_TARGET_FPS,
    max_frames: int = MAX_EXTRACTED_FRAMES,
    jpeg_quality: int = JPEG_QUALITY
) -> Dict[str, Any]:
    """
    Intelligently extract keyframes from a drone video stream.

    Features:
        - Validates video integrity before extraction.
        - Adaptive interval calculation based on video FPS and duration.
        - Automatically throttles target_fps for long videos to prevent
          exceeding max_frames and saturating GPU VRAM / Host RAM.
        - Preserves temporal order and writes frame_metadata.json.
        - Preserves high visual fidelity with JPEG quality 95.

    Returns:
        Dictionary of extraction statistics and output paths.
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Validate stream
    meta = validate_video(video_path)
    fps = meta["fps"]
    total_frames = meta["total_frames"]
    duration = meta["duration_seconds"]

    # 2. Adaptive interval calculation
    if interval is not None:
        effective_interval = max(1, interval)
        logger.info(f"Using manual fixed frame interval: {effective_interval}")
    else:
        # Check if nominal extraction would exceed max_frames ceiling
        estimated_nominal = int(duration * target_fps)
        if estimated_nominal > max_frames and duration > 0:
            adaptive_target_fps = max(0.5, max_frames / duration)
            effective_interval = max(1, int(round(fps / adaptive_target_fps)))
            logger.info(
                f"Adaptive extraction engaged: duration {duration:.1f}s would yield ~{estimated_nominal} frames. "
                f"Throttled target FPS from {target_fps} to {adaptive_target_fps:.2f} "
                f"(interval {effective_interval}) to keep within {max_frames} frames."
            )
        else:
            effective_interval = max(1, int(round(fps / target_fps))) if (fps > 0 and target_fps > 0) else 5
            logger.info(f"Target FPS: {target_fps:.2f} | Frame interval: {effective_interval} (from {fps:.2f} FPS)")

    # 3. Stream & save frames
    cap = cv2.VideoCapture(str(video_path))
    frame_number = 0
    saved_frames = 0
    frame_records = []
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]

    try:
        while True:
            success, frame = cap.read()
            if not success or frame is None:
                break

            if frame_number % effective_interval == 0:
                filename = f"frame_{saved_frames:06d}.jpg"
                output_file = output_dir / filename
                cv2.imwrite(str(output_file), frame, encode_params)

                timestamp_sec = round(frame_number / fps, 3) if fps > 0 else 0.0
                frame_records.append({
                    "frame_index": saved_frames,
                    "source_frame_number": frame_number,
                    "timestamp_sec": timestamp_sec,
                    "filename": filename
                })
                saved_frames += 1

                if saved_frames >= max_frames:
                    logger.info(f"Reached maximum frame limit of {max_frames}. Halting extraction.")
                    break

            frame_number += 1

    finally:
        cap.release()

    if saved_frames == 0:
        raise RuntimeError(f"No frames could be extracted from video '{video_path.name}'.")

    # 4. Save metadata manifest
    metadata_manifest = {
        "video": meta,
        "extraction": {
            "effective_interval": effective_interval,
            "target_fps": target_fps,
            "frames_saved": saved_frames,
            "jpeg_quality": jpeg_quality,
            "output_directory": str(output_dir)
        },
        "frames": frame_records
    }
    manifest_path = output_dir / "frame_metadata.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(metadata_manifest, f, indent=2)

    logger.info(f"Extraction complete: {saved_frames} frames saved to {output_dir}")

    return {
        "total_frames": total_frames,
        "fps": fps,
        "width": meta["width"],
        "height": meta["height"],
        "duration_seconds": duration,
        "frame_interval": effective_interval,
        "frames_saved": saved_frames,
        "output_directory": str(output_dir),
        "codec": meta["codec"],
        "metadata_file": str(manifest_path)
    }
