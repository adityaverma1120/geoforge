# 07 — Video and frame preprocessing

## Backend extraction
`backend/frame_processing.py` contains `extract_frames`. The API worker requests a target sampling rate of 2 frames/second, rather than extracting every source frame. The module returns video metadata including frame counts, FPS, dimensions, and duration (as consumed by `main.py`).

## Quality filtering
`backend/frame_filtering.py` exposes:
- `calculate_sharpness(image_path)`: sharpness score based on image analysis.
- `calculate_brightness(image_path)`: brightness metric.
- `filter_sharp_frames(...)`: applies configured threshold and filtering behavior, including reported blur and brightness removals.

The API passes a threshold of 100.0. This is an implementation parameter, not a universal image-quality standard.

## Redundancy filtering
`backend/redundancy_filter.py` exposes `calculate_difference` and `remove_redundant_frames`. The API passes a difference threshold of 5.0. The aim is to reduce near-duplicate images while preserving useful camera movement/baseline variation.

## Standalone scripts under root `src/`
These scripts are manual/experimental and use relative input/output folders:
- `extract_frames.py` uses `../input/drone_video.mp4` and writes `../frames`.
- `detect_blur.py` evaluates Laplacian variance and writes `../good_frames`, threshold 300.
- `analyze_sharpness.py` prints score distribution.
- `remove_redundant.py` uses template correlation threshold 0.98 and writes `../selected_frames`.

These settings differ from the active backend modules and should not be assumed to be the same production pipeline.
