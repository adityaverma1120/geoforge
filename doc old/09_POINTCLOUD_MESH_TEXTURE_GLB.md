# 09 — Point cloud, mesh, texture, and GLB

## Point-cloud cleanup
The reconstruction module includes point-cloud cleaning and statistics logic. A standalone `clean_pointcloud.py` utility also exists. The exact cleaning parameters and whether every branch is used depend on the pipeline path; inspect the source before adjusting.

## Meshing
`poisson_mesh_with_trimming` uses Open3D's Poisson surface reconstruction where available and may return a signal for a COLMAP `poisson_mesher` fallback. The output is a mesh approximation derived from the dense cloud. Poisson meshing can create surfaces in poorly observed regions; trimming and visual inspection matter.

## Texturing
The reconstruction flow invokes COLMAP mesh texturing and locates the resulting textured model and image asset. The API then selects a PNG/JPG texture candidate.

## GLB conversion
`backend/convert_to_glb.py`:
- Accepts a textured PLY/model path, texture image, and destination.
- Loads geometry with Trimesh and texture with Pillow.
- Attempts to attach UV/material texture data.
- Exports GLB.
- Checks that output exists and is non-empty.
- Logs a warning when UV mapping is missing and may export geometry without a visible texture.

## Viewer
`frontend/src/components/ThreeDViewer.tsx` uses Three.js and GLTF/GLB loading logic. It includes loading progress and checks for invalid dimensions/no visible geometry. Verify camera framing, controls, resize behavior, cleanup, and error paths in browser tests.
