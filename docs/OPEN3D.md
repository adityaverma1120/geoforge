# Open3D Geometry Processing Specification — GeoForge

> **Document:** `docs/OPEN3D.md`  
> **Status:** Code-Verified Open3D Specification (Phase 3 Verified)  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Source Verification Date:** 2026-11-11  
> **Related Documents:** [`docs/RECONSTRUCTION_PIPELINE.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/RECONSTRUCTION_PIPELINE.md), [`docs/COLMAP.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/COLMAP.md), [`docs/MESH_AND_GLB.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/MESH_AND_GLB.md)

---

## 1. Role in Architecture

Open3D (`open3d >= 0.18.0`) is responsible for post-photogrammetry dense point cloud cleaning, normal estimation, and surface mesh generation via Screened Poisson Surface Reconstruction with boundary trimming.

Orchestrated in `backend/reconstruction.py`, Open3D operates directly on `colmap/dense/fused.ply` to produce `colmap/dense/fused_cleaned.ply` and `colmap/mesh/poisson_mesh.ply`.

---

## 2. Statistical Outlier Removal (`backend/reconstruction.py:541-603`)

### 2.1 Implementation
```python
def clean_point_cloud(input_ply: Path, output_ply: Path) -> dict:
    try:
        import open3d as o3d
    except ImportError:
        logger.warning("Open3D is not installed. Skipping point cloud cleaning.")
        shutil.copy2(input_ply, output_ply)
        return {"original_points": -1, "cleaned_points": -1, "removed_points": 0, "skipped": True}

    pcd = o3d.io.read_point_cloud(str(input_ply))
    original_count = len(pcd.points)

    cleaned, inlier_mask = pcd.remove_statistical_outlier(
        nb_neighbors=OUTLIER_NB_NEIGHBORS,  # 20
        std_ratio=OUTLIER_STD_RATIO         # 2.0
    )

    o3d.io.write_point_cloud(str(output_ply), cleaned)
    return {
        "original_points": original_count,
        "cleaned_points": len(cleaned.points),
        "removed_points": original_count - len(cleaned.points)
    }
```

### 2.2 Mathematical Logic
For each point $p_i$, the mean distance $\bar{d}_i$ to its $k = 20$ nearest neighbors is computed:
$$\mu_d = \frac{1}{N} \sum_{i=1}^N \bar{d}_i, \quad \sigma_d = \sqrt{\frac{1}{N} \sum_{i=1}^N (\bar{d}_i - \mu_d)^2}$$
- **Threshold:** Any point with $\bar{d}_i > \mu_d + 2.0 \sigma_d$ is classified as an outlier and removed.
- **Result:** Prunes floating camera artifacts, isolated vegetation noise, and erroneous sky points prior to meshing.

---

## 3. Screened Poisson Meshing & Density Trimming (`backend/reconstruction.py:609-700`)

### 3.1 Implementation
```python
def poisson_mesh_with_trimming(
    input_ply: Path,
    output_ply: Path,
    depth: int = POISSON_DEPTH,             # 11
    density_percentile: float = POISSON_TRIM # 7.0
) -> dict:
    import open3d as o3d
    import numpy as np

    pcd = o3d.io.read_point_cloud(str(input_ply))

    # 1. Normal Estimation
    if not pcd.has_normals():
        pcd.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
        )
        pcd.orient_normals_consistent_tangent_plane(k=15)

    # 2. Poisson Reconstruction
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=depth, linear_fit=True
    )

    # 3. Density-Based Boundary Trimming
    if density_percentile > 0:
        densities_np = np.asarray(densities)
        density_threshold = np.percentile(densities_np, density_percentile)
        vertices_mask = densities_np >= density_threshold
        mesh.remove_vertices_by_mask(~vertices_mask)

    # 4. Geometry Cleanup
    mesh.remove_degenerate_triangles()
    mesh.remove_unreferenced_vertices()

    o3d.io.write_triangle_mesh(str(output_ply), mesh)
    return {
        "vertices": len(mesh.vertices),
        "faces": len(mesh.triangles),
        "density_percentile": density_percentile
    }
```

### 3.2 The Poisson "Ballooning" Problem & Solution
- **The Issue:** Screened Poisson surface reconstruction computes an indicator function $\chi$ over a regular octree ($2^{11} = 2048$ resolution). Because it enforces a closed watertight surface, it naturally creates smooth enclosing hulls (bubbles) over unobserved areas.
- **The Solution:** The algorithm returns the scalar evaluation density at every vertex. Evaluating the density distribution and trimming the lowest 7.0% (`density_percentile = 7.0`) prunes these empty mathematical envelope artifacts, isolating the true physical structure.

---

## 4. Fallback Execution Path (`backend/reconstruction.py:1410-1429`)

If Open3D or NumPy is missing or raises an `ImportError`:
- `poisson_mesh_with_trimming` returns `None`.
- The worker catches this signal and immediately triggers COLMAP's native `poisson_mesher` CLI:
  ```bash
  colmap poisson_mesher \
    --input_path colmap/dense/fused.ply \
    --output_path colmap/mesh/poisson_mesh.ply \
    --PoissonMeshing.depth 11 \
    --PoissonMeshing.trim 7
  ```
- This ensures pipeline resilience across minimal deployment environments.
