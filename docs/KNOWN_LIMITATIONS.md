# GeoForge — Known Limitations, Edge Cases & Hardware Bounds

> **Document:** `KNOWN_LIMITATIONS.md`  
> **Status:** Authoritative Engineering Evaluation  
> **Last Verified:** 2026-11-11  
> **Classification:** Production Boundary Analysis

---

## 1. Overview

GeoForge is designed for automated photogrammetric 3D reconstruction from single-pass continuous drone videos. Photogrammetry relies on fundamental principles of computer vision, epipolar geometry, and numerical optimization. Consequently, reconstruction quality is bounded by the visual content of the input video and the physical resources of the host machine.

This document enumerates the verified operational limits, known edge cases, and architectural constraints of the system.

---

## 2. Input Footage Constraints & Failure Modes

### 2.1 Video Ingestion Boundaries

| Parameter | Operational Limit | Pipeline Behavior Upon Violation |
|---|---|---|
| **Max File Size** | 4.0 GiB (`4 * 1024 * 1024 * 1024` bytes) | HTTP 413 Payload Too Large returned immediately before streaming to disk. |
| **Containers Whitelisted** | `.mp4`, `.mov`, `.avi`, `.mkv` | HTTP 400 Bad Request; non-video extensions rejected. |
| **Decodability** | Must open via `cv2.VideoCapture` | HTTP 400 Bad Request if codec headers are corrupt or unsupported. |
| **Minimum Video Duration** | ~10 seconds at $\ge 20$ FPS | Results in $<20$ extracted frames; triggers Minimum Frame Guard error. |

### 2.2 Scene Visual Content & Texture Edge Cases

Photogrammetric Structure-from-Motion (SfM) requires detecting and matching salient visual keypoints across overlapping frames:

1. **Featureless Surfaces:**
   - **Open Water / Oceans / Lakes:** Specular reflections, moving waves, and uniform luminance prevent stable SIFT keypoint detection.
   - **Overcast Skies / Fog:** Uniform gray background provides zero feature gradients.
   - **Uniform Sand / Snow / Asphalt:** Monochromatic terrain without distinct visual contrast causes feature matcher starvation.
   - **Result:** COLMAP mapper fails at Step 4/11 with `RuntimeError: Sparse reconstruction quality is too poor to continue (registered images < 30%)`.

2. **Specular & Highly Reflective Materials:**
   - Modern glass curtain walls and chrome metal reflect the environment differently as the camera position changes.
   - Violation of the Lambertian surface assumption breaks dense stereo photometric consistency, leading to holes or noise in the point cloud.

3. **Dynamic / Moving Objects:**
   - Moving cars, walking pedestrians, or swaying tree canopies in strong wind violate the static world assumption.
   - Moving elements will either be filtered out as statistical outliers or create ghosting artifacts.

---

## 3. Flight Pattern & Camera Movement Constraints

### 3.1 Unsuitable Flight Trajectories

| Flight Behavior | Consequence | Guidance |
|---|---|---|
| **Stationary Hover (0 m/s)** | Redundancy filter removes up to 50% of frames; remaining frames lack parallax baseline, preventing depth triangulation. | The drone must translate through 3D space (orbit, linear flyover, or grid). |
| **Pure In-Place Yaw Rotation** | Panoramic rotation without translation creates a zero-baseline condition where 3D depth cannot be solved. | Combine yaw rotation with smooth orbital or forward movement. |
| **High-Speed Erratic Maneuvering** | Severe motion blur reduces image gradient sharpness below the Laplacian variance threshold ($<100.0$). | Fly at steady velocity ($2\text{--}5\text{ m/s}$) with high shutter speed ($\ge 1/500\text{s}$). |
| **Rapid Gimbal Pitch Changes** | Radical perspective shifts break sequential feature tracking ($>30^\circ$ jump between adjacent frames). | Maintain steady $45^\circ$ to $60^\circ$ oblique camera pitch. |

---

## 4. Hardware Bounds & Resource Consumption

### 4.1 GPU VRAM Capacity
The dense multi-view stereo phase (COLMAP PatchMatch) is the most VRAM-intensive operation:
- **Baseline Configuration (NVIDIA RTX 3050 Laptop GPU, 6 GB VRAM):**
  - Handles up to 2400 px image dimensions at standard depth levels.
  - Exceeding 4K image dimensions without downsampling will trigger `CUDA error: out of memory`.
  - For high frame counts ($>300$ images), `PATCHMATCH_MAX_IMAGE_SIZE` is capped at `2000` to maintain safe GPU headroom.

### 4.2 System RAM & Worker Concurrency
- **Single Worker Lock:**
  - Because COLMAP utilizes all available CPU threads during feature extraction and dense stereo fusion, the backend enforces `MAX_CONCURRENT_RECONSTRUCTIONS = 1`.
  - Attempting to process multiple jobs simultaneously on a 16 GB machine will saturate memory and trigger swap paging.

### 4.3 Storage Footprint
- An active reconstruction generates intermediate depth maps, normal maps, and point clouds requiring **3 to 5 GB** of temporary disk storage per job.
- Systems with less than 10 GB of free disk space will be flagged as degraded in `/health`.

---

## 5. Metric Scale & Georeferencing Status

1. **Unscaled Coordinate Space:**
   - Monocular drone video lacks absolute physical scale (scale ambiguity in SfM).
   - The resulting 3D models are reconstructed with accurate internal proportions and angles, but overall scale is arbitrary.
   - **Roadmap:** Scale calibration via Ground Control Points (GCPs) or flight telemetry is scheduled for future milestones.

2. **No Georeferencing / RTK Integration:**
   - The output binary GLB is in local Cartesian coordinates (centered at the origin).
   - Geographic coordinates (WGS84, UTM), GeoTIFF orthomosaics, and georeferenced LAS point clouds are not yet generated in the current release.

---

## 6. Geometric & Meshing Boundaries

1. **Watertight Poisson Meshing:**
   - Open3D screened Poisson surface reconstruction creates closed, watertight manifold surfaces.
   - Non-surface objects (thin antenna masts, individual power cables, fine tree twigs) are smoothed or merged into surrounding geometry.
2. **Poisson Boundary Trimming:**
   - The pipeline applies a `POISSON_TRIM = 7.0` percentile density trim to remove low-density extrapolation bubbles around the reconstruction boundaries.
   - Ground edges may appear scalloped where camera coverage ended.

---

## 7. WebGL & Client Viewer Boundaries

1. **Browser Memory Caps:**
   - Models with over 1,000,000 triangles or texture atlases exceeding 4096x4096px may cause WebGL context losses on mobile devices or low-end integrated GPUs.
   - The default GeoForge export target is optimized for **100,000 to 300,000 triangles** and **2 to 15 MB GLB size**, ensuring 60 FPS rendering in Three.js across modern laptops and desktop browsers.
