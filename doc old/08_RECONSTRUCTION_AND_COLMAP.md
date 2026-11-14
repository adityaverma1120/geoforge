# 08 — COLMAP reconstruction

## Role
COLMAP is the photogrammetry engine. `backend/reconstruction.py` orchestrates its command-line steps and parses model outputs/stats.

## Configuration
- Executable from `COLMAP_EXE`; default in source: `C:\bin\colmap.exe`.
- Source checks that the executable exists and can be started.
- COLMAP vocabulary tree assets are searched beside the executable using known candidate filenames. Ensure the required vocabulary asset exists for the configured workflow.
- Windows paths are normalized for command invocation.

## Pipeline concepts
1. Create/clean a COLMAP database and register images.
2. Extract image features.
3. Match image features.
4. Run mapper / sparse camera reconstruction.
5. Select a suitable sparse model if multiple model directories are created.
6. Run dense image undistortion and stereo/depth-map reconstruction.
7. Fuse depth maps into a dense point cloud.
8. Clean cloud / mesh, then texture the mesh.

Exact command flags and thresholds are implementation details inside `reconstruction.py`; inspect the current file before changing them. Do not treat this conceptual list as a claim that every run completes every stage.

## Outputs
The worker expects a textured-model artifact and then creates `model.glb` in the textured directory. It also reports paths/stats for sparse/dense cloud, mesh, and model.

## Quality caveats
COLMAP can fail or produce incomplete/fragmented models when footage has low overlap, blur, low texture, changing illumination, moving objects, repetitive surfaces, weak camera movement, or insufficient frame count. A visually plausible result is not automatically geospatially calibrated or metrically accurate.
