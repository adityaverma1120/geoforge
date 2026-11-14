# 20 — Glossary

- **Photogrammetry:** Estimating 3D structure from overlapping images.
- **Frame:** A still image extracted from a video.
- **Sharpness score:** Image metric used to estimate blur; thresholds are implementation-specific.
- **Redundancy filter:** Selects images with sufficient visual difference from previous selected frames.
- **COLMAP:** Photogrammetry and structure-from-motion / multi-view-stereo software.
- **Sparse reconstruction:** Camera poses and sparse 3D points inferred from matched image features.
- **Dense point cloud:** Large set of 3D points representing observed surfaces.
- **Poisson mesh:** Surface reconstructed from oriented point cloud data using Poisson reconstruction.
- **Texture:** Image mapped onto mesh surface using UV coordinates.
- **PLY:** Polygon File Format commonly used for point clouds and meshes.
- **GLB:** Binary glTF format that can package 3D geometry, materials, and texture assets.
- **Job ID:** Identifier for a reconstruction task; currently associated with in-memory backend job metadata.
- **CORS:** Browser policy controlling which origins may call a backend.
- **AGL:** Above ground level; appears in UI capture tips, not a guaranteed flight instruction.
