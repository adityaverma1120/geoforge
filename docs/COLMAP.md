# COLMAP Integration & Configuration Specification — GeoForge

> **Document:** `docs/COLMAP.md`  
> **Status:** Code-Verified COLMAP Specification (Phase 3 Verified)  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Source Verification Date:** 2026-11-11  
> **Related Documents:** [`docs/RECONSTRUCTION_PIPELINE.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/RECONSTRUCTION_PIPELINE.md), [`docs/OPEN3D.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/OPEN3D.md), [`docs/MESH_AND_GLB.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/MESH_AND_GLB.md)

---

## 1. Role & Architecture in GeoForge

COLMAP is the primary photogrammetric Structure-from-Motion (SfM) and Multi-View Stereo (MVS) engine in GeoForge. Orchestrated by `backend/reconstruction.py`, COLMAP executes 7 core commands:
1. `colmap feature_extractor`
2. `colmap sequential_matcher`
3. `colmap mapper`
4. `colmap image_undistorter`
5. `colmap patch_match_stereo`
6. `colmap stereo_fusion`
7. `colmap mesh_texturer` (and fallback `colmap poisson_mesher`)

---

## 2. Executable Discovery & Space-Safe Subprocess Execution

### 2.1 Executable Resolution (`backend/reconstruction.py:17`)
```python
COLMAP = os.environ.get("COLMAP_EXE", r"C:\bin\colmap.exe")
```
- Discovered from `COLMAP_EXE` environment variable, falling back to default Windows path `C:\bin\colmap.exe`.
- Validated prior to execution via `check_colmap()` (`reconstruction.py:108-129`).

### 2.2 Space-Safe Execution Architecture (`backend/reconstruction.py:149-242`)
Windows batch scripts (`COLMAP.bat`, `cmd.exe /c`, `CALL`) fail when developer paths contain spaces (e.g. `C:\Users\Aditya verma\...`).
To guarantee stability, `reconstruction.py:run_colmap`:
- Executes the compiled binary directly (`shell=False`).
- Passes arguments as a structured Python list: `cmd = [COLMAP, command] + clean_args`.
- Streams stdout and stderr line-by-line via `subprocess.Popen(..., stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")`.
- If returncode $\ne 0$, raises `RuntimeError` capturing the last 120 lines of COLMAP terminal logs.

---

## 3. Verified Configuration Parameters (`backend/reconstruction.py:26-92`)

| Constant | Value | Purpose & Photogrammetric Rationale |
|---|---|---|
| `CAMERA_MODEL` | `"OPENCV"` | 8 intrinsic parameters ($f_x, f_y, c_x, c_y, k_1, k_2, p_1, p_2$). Accurately models both radial and tangential lens distortion common in drone cameras. |
| `MAX_NUM_FEATURES` | `16384` | SIFT feature count (increased from default 8192) to ensure dense correspondence across repetitive terrain (foliage, asphalt, roofs). |
| `SEQUENTIAL_OVERLAP` | `15` | Matches each frame against 15 neighboring frames forward and backward. |
| `FORCE_SINGLE_MODEL` | `True` | Passes `--Mapper.multiple_models 0` to prevent COLMAP from fragmenting the flight path into disconnected components. |
| `MIN_REGISTRATION_RATIO` | `0.30` (30%) | Sparse quality gate: fails early if fewer than 30% of frames are registered. |
| `PATCHMATCH_MAX_IMAGE_SIZE`| `2400` | Limits maximum image dimension during dense PatchMatch stereo to balance depth resolution against GPU VRAM. |
| `PATCHMATCH_NUM_ITERATIONS`| `7` | Number of PatchMatch iterations (increased from default 5) for consistent depth estimation. |
| `FUSION_MIN_NUM_PIXELS` | `3` | Minimum pixel agreement across stereo pairs for depth fusion (preserves boundary details). |
| `FUSION_MAX_REPROJ_ERROR` | `2.0` | Maximum reprojection error in pixels for fused points. |
| `POISSON_DEPTH` | `11` | Octree depth for Poisson meshing ($2^{11} = 2048$ resolution). |
| `POISSON_TRIM` | `7.0` | Prunes bottom 7.0% density vertices to eliminate unconstrained boundary hulls. |
| `OUTLIER_NB_NEIGHBORS` | `20` | Statistical outlier removal neighbor count. |
| `OUTLIER_STD_RATIO` | `2.0` | Standard deviation multiplier for distance thresholding. |

---

## 4. Vocabulary Tree Candidate Discovery (`backend/reconstruction.py:952-965`)

For loop closure detection during sequential matching, `reconstruction.py` checks 5 standard candidate paths:
1. `Path(COLMAP).parent / "vocab_tree_flickr100K_words256K.bin"`
2. `Path(COLMAP).parent / "vocab_tree_flickr100K_words32K.bin"`
3. `Path(COLMAP).parent / "vocab_tree-65536.bin"`
4. `Path(r"C:\bin\vocab_tree_flickr100K_words256K.bin")`
5. `Path(r"C:\bin\vocab_tree_flickr100K_words32K.bin")`

- **If Found:** Enables loop detection: `--SequentialMatching.loop_detection 1 --SequentialMatching.vocab_tree_path <path>`.
- **If Absent:** Logs informational message and proceeds with sequential neighborhood matching.

---

## 5. Binary Model Parsing & Sparse Quality Gate (`backend/reconstruction.py:315-372, 1060-1122`)

Before allocating GPU time to dense MVS, `reconstruction.py` parses the binary model headers:
- `cameras.bin`: Reads total camera models using `struct.unpack("<Q", f.read(8))[0]`.
- `images.bin`: Reads registered image count using `struct.unpack("<Q", f.read(8))[0]`.
- `points3D.bin`: Reads triangulated sparse 3D point count using `struct.unpack("<Q", f.read(8))[0]`.

### Quality Gate Evaluation
$$\text{Registration Ratio} = \frac{\text{num\_registered\_images}}{\text{num\_input\_images}}$$
- If $\text{Registration Ratio} < 0.30$, raises `RuntimeError` immediately with capture remediation tips.
- If $\text{Registration Ratio} < 0.70$, adds a warning to `quality_warnings` list.
- If $\text{num\_points3D} < 1000$, adds a warning regarding low point density.

---

## 6. Dense Reconstruction & Texturing Invocation

### 6.1 Dense MVS Command Flow
1. **Undistort:**
   `colmap image_undistorter --image_path final_frames --input_path sparse/0 --output_path dense --output_type COLMAP`
2. **PatchMatch:**
   `colmap patch_match_stereo --workspace_path dense --workspace_format COLMAP --PatchMatchStereo.geom_consistency 1 --PatchMatchStereo.max_image_size 2400 --PatchMatchStereo.num_iterations 7 --PatchMatchStereo.gpu_index 0`
3. **Stereo Fusion:**
   `colmap stereo_fusion --workspace_path dense --workspace_format COLMAP --input_type geometric --output_type PLY --output_path dense/fused.ply --StereoFusion.min_num_pixels 3 --StereoFusion.max_reproj_error 2.0`

### 6.2 Mesh Texturing Invocation
`colmap mesh_texturer --workspace_path dense --input_path mesh/poisson_mesh.ply --output_path textured`
- Emits vertex-colored `model.ply`, UV-mapped `model.obj`, material file `model.mtl`, and diffuse atlas `model.png`.
