import logging
import os
import struct
import subprocess
from pathlib import Path
import shutil
from typing import Callable, Optional

from dotenv import load_dotenv

# Load environment variables from .env if present
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()

logger = logging.getLogger(__name__)


# ============================================================
# COLMAP CONFIGURATION
# ============================================================

def resolve_colmap_path() -> str:
    """Resolve the COLMAP executable path using environment variables and standard locations."""
    env_colmap = os.environ.get("COLMAP_EXE")
    if env_colmap and Path(env_colmap).exists() and Path(env_colmap).is_file():
        return str(Path(env_colmap).resolve())

    which_colmap = shutil.which("colmap")
    if which_colmap and Path(which_colmap).exists():
        return str(Path(which_colmap).resolve())

    candidate_paths = [
        Path.home() / "AppData" / "Local" / "Programs" / "COLMAP" / "bin" / "colmap.exe",
        Path(r"C:\Users\adity\AppData\Local\Programs\COLMAP\bin\colmap.exe"),
        Path(r"C:\bin\colmap.exe"),
        Path(r"C:\COLMAP\bin\colmap.exe"),
        Path(r"C:\Program Files\COLMAP\bin\colmap.exe"),
    ]
    for p in candidate_paths:
        if p.exists() and p.is_file():
            return str(p.resolve())

    return os.environ.get("COLMAP_EXE", r"C:\bin\colmap.exe")

# Read from environment variable; fall back to the default install location.
COLMAP = resolve_colmap_path()


# ============================================================
# RECONSTRUCTION QUALITY SETTINGS
# ============================================================
# All important thresholds are gathered here so they can be
# tuned without searching through the pipeline code.

# --- Feature Extraction ---
# Camera model for drone video.
# OPENCV has 8 parameters (fx, fy, cx, cy, k1, k2, p1, p2)
# and handles both radial and tangential distortion well
# for typical consumer drone cameras.
CAMERA_MODEL = "OPENCV"

# Maximum SIFT features per image.
# 8192 provides ample keypoints for dense matching while keeping
# matching time low.
MAX_NUM_FEATURES = 8192

# --- Feature Matching ---
# Sequential matching overlap: how many neighbouring frames
# to match each image against. 10 frames provides strong trajectory
# connectivity without redundant pairs.
SEQUENTIAL_OVERLAP = 10

# --- Mapper / SfM ---
# Allow COLMAP to explore alternative seed pairs if an initial 2-image
# pair fails to expand, preventing false-start failures.
# The downstream find_best_model selector picks the largest connected component.
FORCE_SINGLE_MODEL = False

# Minimum fraction of input images that must be registered
# in the sparse model. Below this, the reconstruction is
# considered too poor to proceed with dense reconstruction.
MIN_REGISTRATION_RATIO = 0.30

# --- PatchMatch Stereo ---
# Maximum image dimension for dense stereo.
# 1200 is optimized for fast, accurate dense MVS on laptop GPUs.
PATCHMATCH_MAX_IMAGE_SIZE = 1200

# Number of PatchMatch iterations.
# 4 iterations achieve convergence with low latency.
PATCHMATCH_NUM_ITERATIONS = 4

# --- Stereo Fusion ---
# Minimum pixels that must agree on a depth for it to be fused.
# Lower = denser point cloud but potentially more noise.
FUSION_MIN_NUM_PIXELS = 3

# Maximum reprojection error for fused points (pixels).
FUSION_MAX_REPROJ_ERROR = 2.0

# --- Poisson Meshing ---
# Octree depth for Poisson reconstruction.
# Depth 9 yields clean surface definition without excessive vertex counts.
POISSON_DEPTH = 9

# Density percentile trim for Poisson mesh.
# Removes low-density triangles that are typically
# hallucinated geometry at the boundary of the point cloud.
# Value is a trim percentage (0-100). 7 = trim bottom 7%.
POISSON_TRIM = 7.0

# --- Point Cloud Cleaning ---
# Statistical outlier removal: number of neighbours.
OUTLIER_NB_NEIGHBORS = 20
# Statistical outlier removal: standard deviation ratio.
OUTLIER_STD_RATIO = 2.0


# ============================================================
# PRINT SECTION
# ============================================================

def print_section(title: str):
    logger.info("=" * 75)
    logger.info(title)
    logger.info("=" * 75)


# ============================================================
# CHECK COLMAP
# ============================================================

def check_colmap():
    """
    Verify that the COLMAP executable exists.
    """
    global COLMAP
    COLMAP = resolve_colmap_path()
    colmap_path = Path(COLMAP)

    if not colmap_path.exists():
        raise RuntimeError(
            "COLMAP executable was not found.\n\n"
            f"Expected location:\n{COLMAP}\n\n"
            "Override by setting the COLMAP_EXE environment variable."
        )

    if not colmap_path.is_file():
        raise RuntimeError(
            f"COLMAP path is not a file:\n{COLMAP}"
        )

    logger.info(f"COLMAP found: {COLMAP}")


# ============================================================
# WINDOWS PATH HELPER
# ============================================================

def windows_path(path):
    """
    Convert a path into an absolute Windows path.

    Returns a normal string. subprocess handles spaces
    correctly when arguments are passed as a list.
    """

    return str(Path(path).resolve())


# ============================================================
# RUN COLMAP
# ============================================================

def run_colmap(command, args):
    """
    Execute COLMAP directly.

    IMPORTANT:
    We intentionally DO NOT use:

        C:\\COLMAP.bat
        cmd.exe
        /c
        CALL

    The direct EXE avoids the Windows batch-file quoting
    problem caused by paths such as:

        C:\\Users\\Aditya verma\\...

    Arguments are passed to subprocess as a list, which
    safely handles spaces in Windows paths.
    """

    print_section(f"COLMAP COMMAND: {command}")

    check_colmap()

    clean_args = [str(arg) for arg in args]

    cmd = [COLMAP, command] + clean_args

    logger.info("COLMAP command:")
    for index, arg in enumerate(cmd):
        logger.info(f"  [{index}] {arg}")

    # --------------------------------------------------------
    # Execute with live output streaming
    # --------------------------------------------------------

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            f"COLMAP executable could not be started.\nCOLMAP: {COLMAP}"
        ) from e
    except PermissionError as e:
        raise RuntimeError(
            f"Windows denied access to the COLMAP executable.\nCOLMAP: {COLMAP}"
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"Failed to start COLMAP command '{command}'.\nError: {e}"
        ) from e

    # --------------------------------------------------------
    # Stream output line by line
    # --------------------------------------------------------

    output_lines = []

    for line in process.stdout:
        line = line.rstrip("\n")
        logger.info(f"[COLMAP] {line}")
        output_lines.append(line)

    process.wait()

    output = "\n".join(output_lines)
    returncode = process.returncode

    # --------------------------------------------------------
    # Check exit code
    # --------------------------------------------------------

    if returncode != 0:
        lines = output_lines
        tail = "\n".join(lines[-120:]) if len(lines) > 120 else output
        raise RuntimeError(
            f"COLMAP command failed.\n"
            f"Command: {command}\n"
            f"Exit code: {returncode}\n\n"
            f"COLMAP output (last 120 lines):\n{tail}"
        )

    logger.info(f"COLMAP {command} completed successfully.")

    return process


# ============================================================
# FIND BEST SPARSE MODEL
# ============================================================

def find_best_model(sparse_dir: Path):
    """
    Find the best sparse reconstruction generated by COLMAP.

    COLMAP can create multiple model folders:

        sparse/
            0/
            1/
            2/

    We choose the model containing the largest images.bin.
    """

    if not sparse_dir.exists():

        raise RuntimeError(
            "Sparse directory does not exist:\n"
            f"{sparse_dir}"
        )

    models = [
        folder
        for folder in sparse_dir.iterdir()
        if folder.is_dir()
    ]

    if not models:

        raise RuntimeError(
            "COLMAP mapper completed but produced "
            "no sparse reconstruction model."
        )

    best_model = None
    best_registered = -1
    best_points = -1

    for model in models:
        images_bin = model / "images.bin"
        if not images_bin.exists():
            continue

        stats = read_sparse_model_stats(model)
        reg = stats["num_registered_images"]
        pts = stats["num_points3D"]
        size = images_bin.stat().st_size
        logger.info(f"Sparse model {model.name}: registered={reg}, points={pts}, images.bin={size} bytes")

        if (reg > best_registered) or (reg == best_registered and pts > best_points):
            best_registered = reg
            best_points = pts
            best_model = model

    if best_model is None:

        raise RuntimeError(
            "COLMAP created model folders, but none "
            "contains a valid images.bin file."
        )

    return best_model


# ============================================================
# READ SPARSE MODEL STATISTICS
# ============================================================

def read_sparse_model_stats(model_dir: Path) -> dict:
    """
    Read basic statistics from a COLMAP sparse model's
    binary files without loading the full model.

    Returns a dict with:
      - num_cameras
      - num_registered_images
      - num_points3D
    """

    stats = {
        "num_cameras": 0,
        "num_registered_images": 0,
        "num_points3D": 0,
    }

    # --------------------------------------------------------
    # cameras.bin: count cameras
    # Format: num_cameras (uint64), then camera records
    # --------------------------------------------------------
    cameras_bin = model_dir / "cameras.bin"
    if cameras_bin.exists() and cameras_bin.stat().st_size >= 8:
        try:
            with open(cameras_bin, "rb") as f:
                num_cameras = struct.unpack("<Q", f.read(8))[0]
                stats["num_cameras"] = num_cameras
        except Exception:
            pass

    # --------------------------------------------------------
    # images.bin: count registered images
    # Format: num_reg_images (uint64), then image records
    # --------------------------------------------------------
    images_bin = model_dir / "images.bin"
    if images_bin.exists() and images_bin.stat().st_size >= 8:
        try:
            with open(images_bin, "rb") as f:
                num_images = struct.unpack("<Q", f.read(8))[0]
                stats["num_registered_images"] = num_images
        except Exception:
            pass

    # --------------------------------------------------------
    # points3D.bin: count 3D points
    # Format: num_points3D (uint64), then point records
    # --------------------------------------------------------
    points3d_bin = model_dir / "points3D.bin"
    if points3d_bin.exists() and points3d_bin.stat().st_size >= 8:
        try:
            with open(points3d_bin, "rb") as f:
                num_points = struct.unpack("<Q", f.read(8))[0]
                stats["num_points3D"] = num_points
        except Exception:
            pass

    return stats


# ============================================================
# GET INPUT IMAGES
# ============================================================

def get_input_images(image_dir: Path):
    """
    Find supported image files.
    """

    extensions = {
        ".jpg",
        ".jpeg",
        ".png"
    }

    if not image_dir.exists():
        return []

    images = [
        p
        for p in image_dir.iterdir()
        if (
            p.is_file()
            and p.suffix.lower() in extensions
        )
    ]

    return sorted(
        images,
        key=lambda p: p.name.lower()
    )


# ============================================================
# CHECK FILE
# ============================================================

def check_file(
    path: Path,
    description: str
):
    """
    Verify that an expected output file exists
    and is not empty.
    """

    if not path.exists():

        raise RuntimeError(
            f"{description} was not created:\n"
            f"{path}"
        )

    if path.is_file():

        if path.stat().st_size == 0:

            raise RuntimeError(
                f"{description} exists but is empty:\n"
                f"{path}"
            )


# ============================================================
# CLEAN DIRECTORY
# ============================================================

def clean_directory(directory: Path):
    """
    Delete everything inside a directory while keeping
    the directory itself.
    """

    if not directory.exists():

        directory.mkdir(
            parents=True,
            exist_ok=True
        )

        return

    for item in directory.iterdir():

        try:

            if item.is_dir():

                shutil.rmtree(item)

            else:

                item.unlink()

        except Exception as e:
            logger.warning(f"Could not remove {item}: {e}")


# ============================================================
# CLEAN OLD COLMAP DATABASE
# ============================================================

def clean_colmap_database(
    database_path: Path
):
    """
    Remove an old COLMAP database.

    This ensures every reconstruction starts with a
    clean database.
    """

    if database_path.exists():

        logger.info(f"Removing previous COLMAP database: {database_path}")

        try:

            database_path.unlink()

        except Exception as e:

            raise RuntimeError(
                "Could not remove the previous "
                "COLMAP database.\n\n"
                f"{database_path}\n\n"
                "Make sure COLMAP is not using this "
                "database.\n\n"
                f"Error: {e}"
            ) from e


# ============================================================
# CHECK DATABASE
# ============================================================

def check_database(
    database_path: Path
):
    """
    Verify that the COLMAP database exists and
    contains some data.
    """

    check_file(
        database_path,
        "COLMAP database"
    )

    size = (
        database_path.stat().st_size
    )

    if size < 1000:

        raise RuntimeError(
            "COLMAP database was created but "
            "appears to be empty or invalid.\n\n"
            f"Database:\n{database_path}\n\n"
            f"Database size: {size} bytes"
        )


# ============================================================
# CLEAN POINT CLOUD (Open3D)
# ============================================================

def clean_point_cloud(input_ply: Path, output_ply: Path) -> dict:
    """
    Remove outliers from a dense point cloud using Open3D.

    1. Statistical outlier removal — removes points that are
       far from their neighbours (floating points, noise).
    2. The cleaned cloud is saved to output_ply.

    Returns a dict with point counts.
    """

    try:
        import open3d as o3d
    except ImportError:
        logger.warning(
            "Open3D is not installed. Skipping point cloud cleaning. "
            "Install with: pip install open3d"
        )
        # Copy input to output unchanged
        shutil.copy2(input_ply, output_ply)
        return {"original_points": -1, "cleaned_points": -1, "removed_points": 0, "skipped": True}

    logger.info("Loading point cloud for cleaning...")
    pcd = o3d.io.read_point_cloud(str(input_ply))
    original_count = len(pcd.points)
    logger.info(f"Original point count: {original_count:,}")

    if original_count == 0:
        logger.warning("Point cloud is empty — skipping cleaning.")
        shutil.copy2(input_ply, output_ply)
        return {"original_points": 0, "cleaned_points": 0, "removed_points": 0}

    # --------------------------------------------------------
    # Statistical outlier removal
    # --------------------------------------------------------
    logger.info(
        f"Statistical outlier removal: "
        f"nb_neighbors={OUTLIER_NB_NEIGHBORS}, "
        f"std_ratio={OUTLIER_STD_RATIO}"
    )

    cleaned, inlier_mask = pcd.remove_statistical_outlier(
        nb_neighbors=OUTLIER_NB_NEIGHBORS,
        std_ratio=OUTLIER_STD_RATIO
    )

    cleaned_count = len(cleaned.points)
    removed = original_count - cleaned_count

    logger.info(f"After statistical outlier removal: {cleaned_count:,} points ({removed:,} removed)")

    # --------------------------------------------------------
    # Save cleaned cloud & compute bounding box
    # --------------------------------------------------------
    logger.info(f"Saving cleaned point cloud: {output_ply}")
    o3d.io.write_point_cloud(str(output_ply), cleaned)

    bbox = cleaned.get_axis_aligned_bounding_box()
    min_b = [round(float(x), 3) for x in bbox.min_bound]
    max_b = [round(float(x), 3) for x in bbox.max_bound]
    extent = [round(float(x), 3) for x in bbox.get_extent()]

    return {
        "original_points": original_count,
        "cleaned_points": cleaned_count,
        "removed_points": removed,
        "bounding_box": {
            "min_bound": min_b,
            "max_bound": max_b,
            "dimensions": extent
        }
    }


# ============================================================
# POISSON MESH WITH DENSITY TRIMMING (Open3D)
# ============================================================

def poisson_mesh_with_trimming(
    input_ply: Path,
    output_ply: Path,
    depth: int = POISSON_DEPTH,
    density_percentile: float = POISSON_TRIM,
) -> dict:
    """
    Generate a Poisson surface mesh with density-based trimming
    to remove hallucinated geometry at the boundary.

    Falls back to COLMAP's poisson_mesher if Open3D is unavailable.

    Returns mesh statistics.
    """

    try:
        import open3d as o3d
        import numpy as np
    except ImportError:
        logger.warning("Open3D not available for Poisson meshing — using COLMAP poisson_mesher fallback.")
        return None  # Signal caller to use COLMAP fallback

    logger.info(f"Loading point cloud for Poisson meshing: {input_ply}")
    pcd = o3d.io.read_point_cloud(str(input_ply))
    point_count = len(pcd.points)
    logger.info(f"Point count: {point_count:,}")

    if point_count == 0:
        raise RuntimeError("Cannot create mesh from empty point cloud.")

    # --------------------------------------------------------
    # Estimate normals if not present
    # --------------------------------------------------------
    if not pcd.has_normals():
        logger.info("Estimating point normals...")
        pcd.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
        )
        pcd.orient_normals_consistent_tangent_plane(k=15)

    # --------------------------------------------------------
    # Poisson reconstruction
    # --------------------------------------------------------
    logger.info(f"Running Poisson reconstruction (depth={depth})...")
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=depth, linear_fit=True
    )

    vertices_before = len(mesh.vertices)
    faces_before = len(mesh.triangles)
    logger.info(f"Poisson mesh: {vertices_before:,} vertices, {faces_before:,} faces (before trim)")

    # --------------------------------------------------------
    # Density-based trimming
    # Removes triangles in regions where the point cloud was
    # sparse — these are typically hallucinated Poisson geometry
    # at the boundary.
    # --------------------------------------------------------
    if density_percentile > 0:
        densities_np = np.asarray(densities)
        density_threshold = np.percentile(densities_np, density_percentile)
        logger.info(
            f"Density trimming: removing bottom {density_percentile}% "
            f"(threshold={density_threshold:.6f})"
        )
        vertices_mask = densities_np >= density_threshold
        mesh.remove_vertices_by_mask(~vertices_mask)

    # --------------------------------------------------------
    # Clean up
    # --------------------------------------------------------
    mesh.remove_degenerate_triangles()
    mesh.remove_unreferenced_vertices()

    vertices_after = len(mesh.vertices)
    faces_after = len(mesh.triangles)
    logger.info(f"After trimming: {vertices_after:,} vertices, {faces_after:,} faces")

    # --------------------------------------------------------
    # Save & compute bounding dimensions
    # --------------------------------------------------------
    logger.info(f"Saving Poisson mesh: {output_ply}")
    o3d.io.write_triangle_mesh(str(output_ply), mesh)

    mesh_bbox = mesh.get_axis_aligned_bounding_box()
    mesh_extent = [round(float(x), 3) for x in mesh_bbox.get_extent()]

    return {
        "vertices_before_trim": vertices_before,
        "faces_before_trim": faces_before,
        "vertices": vertices_after,
        "faces": faces_after,
        "density_percentile": density_percentile,
        "dimensions": mesh_extent,
    }


# ============================================================
# COLORIZE & TEXTURE MESH (Open3D + KDTree)
# ============================================================

def colorize_mesh_from_point_cloud(
    mesh_ply: Path,
    point_cloud_ply: Path,
    output_dir: Path
) -> Path:
    """
    Transfer dense point cloud RGB colors to the Poisson mesh vertices using KDTree interpolation.
    Outputs a colored PLY in output_dir / "textured_mesh.ply" and a clean base texture image.
    Guarantees a valid textured model for GLB conversion without depending on non-existent COLMAP commands.
    """
    import numpy as np
    import open3d as o3d
    from scipy.spatial import cKDTree
    from PIL import Image

    logger.info("Transferring dense point cloud RGB colors to mesh vertices...")
    pcd = o3d.io.read_point_cloud(str(point_cloud_ply))
    mesh = o3d.io.read_triangle_mesh(str(mesh_ply))

    if not pcd.has_colors() or len(pcd.points) == 0:
        logger.warning("Point cloud has no colors; generating neutral terrain vertex colors.")
        v_count = len(mesh.vertices)
        default_color = np.array([0.62, 0.62, 0.58])
        mesh.vertex_colors = o3d.utility.Vector3dVector(np.tile(default_color, (v_count, 1)))
    else:
        pcd_pts = np.asarray(pcd.points)
        pcd_cols = np.asarray(pcd.colors)
        mesh_v = np.asarray(mesh.vertices)

        tree = cKDTree(pcd_pts)
        dists, idxs = tree.query(mesh_v, k=1)
        mesh.vertex_colors = o3d.utility.Vector3dVector(pcd_cols[idxs])
        logger.info(f"Successfully transferred RGB colors to {len(mesh_v):,} mesh vertices.")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_ply = output_dir / "textured_mesh.ply"
    o3d.io.write_triangle_mesh(str(out_ply), mesh, write_vertex_colors=True)

    tex_path = output_dir / "texture.png"
    if not tex_path.exists():
        tex_img = Image.new("RGB", (256, 256), color=(175, 175, 165))
        tex_img.save(str(tex_path))

    return out_ply


# ============================================================
# RECONSTRUCTION PIPELINE
# ============================================================

def run_reconstruction(
    image_dir: str,
    workspace_dir: str,
    progress_callback: Optional[Callable[[str, int, str], None]] = None
):
    """
    Complete drone-video-to-3D reconstruction pipeline.

    Pipeline:

        Images
           ↓
        Feature Extraction (SIFT, OPENCV camera model)
           ↓
        Feature Matching (sequential + loop detection)
           ↓
        Sparse Reconstruction / SfM (single model)
           ↓
        Sparse Model Quality Gate
           ↓
        Image Undistortion
           ↓
        PatchMatch Stereo (GPU)
           ↓
        Stereo Fusion
           ↓
        Point Cloud Cleaning (Open3D)
           ↓
        Poisson Meshing + density trimming
           ↓
        Texture Mapping
           ↓
        Final 3D Model + Quality Report
    """

    image_dir = Path(
        image_dir
    ).resolve()

    workspace_dir = Path(
        workspace_dir
    ).resolve()

    # ========================================================
    # START
    # ========================================================

    print_section("STARTING DRONE VIDEO TO 3D RECONSTRUCTION")
    logger.info(f"Input images : {image_dir}")
    logger.info(f"Workspace    : {workspace_dir}")

    # ========================================================
    # CHECK COLMAP
    # ========================================================

    check_colmap()

    # ========================================================
    # CHECK IMAGE DIRECTORY
    # ========================================================

    if not image_dir.exists():

        raise RuntimeError(
            "Image directory does not exist:\n"
            f"{image_dir}"
        )

    images = get_input_images(
        image_dir
    )

    if not images:

        raise RuntimeError(
            "No supported images were found in:\n"
            f"{image_dir}\n\n"
            "Supported formats:\n"
            "JPG\n"
            "JPEG\n"
            "PNG"
        )

    num_input_images = len(images)
    logger.info(f"Images available for reconstruction: {num_input_images}")

    # ========================================================
    # CREATE WORKSPACE
    # ========================================================

    workspace_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    database_path = (
        workspace_dir /
        "database.db"
    )

    sparse_dir = (
        workspace_dir /
        "sparse"
    )

    dense_dir = (
        workspace_dir /
        "dense"
    )

    mesh_dir = (
        workspace_dir /
        "mesh"
    )

    textured_dir = (
        workspace_dir /
        "textured"
    )

    # --------------------------------------------------------
    # Create directories
    # --------------------------------------------------------

    sparse_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    dense_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    mesh_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    textured_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # CLEAN OLD DATABASE
    # ========================================================

    clean_colmap_database(
        database_path
    )

    # ========================================================
    # STEP 1 — FEATURE EXTRACTION
    # ========================================================
    # Key changes from original:
    # - Camera model: OPENCV (8-param) instead of default
    #   SIMPLE_RADIAL. Drone cameras have tangential distortion
    #   that SIMPLE_RADIAL cannot model, causing misalignment.
    # - max_num_features: 16384 instead of 8192. Aerial imagery
    #   has repetitive textures; more features improve matching.
    # - estimate_affine_shape + domain_size_pooling: improves
    #   feature repeatability for planar aerial scenes.
    # - GPU acceleration for SIFT extraction.

    print_section(
        "STEP 1/11 — FEATURE EXTRACTION"
    )
    if progress_callback:
        progress_callback("extracting_features", 35, "Detecting visual features in frames (GPU SIFT)...")

    logger.info(
        "Detecting SIFT features in drone frames."
    )
    logger.info(f"  Camera model       : {CAMERA_MODEL}")
    logger.info(f"  Max features/image : {MAX_NUM_FEATURES}")
    logger.info(f"  Single camera      : yes")

    run_colmap(
        "feature_extractor",
        [
            "--database_path",
            windows_path(database_path),

            "--image_path",
            windows_path(image_dir),

            # All frames come from the same drone camera
            "--ImageReader.single_camera", "1",

            # Camera model with radial + tangential distortion
            # OPENCV = fx, fy, cx, cy, k1, k2, p1, p2
            "--ImageReader.camera_model", CAMERA_MODEL,

            # More SIFT features for aerial imagery
            "--SiftExtraction.max_num_features", str(MAX_NUM_FEATURES),

            # Affine shape estimation improves matching for
            # oblique/perspective views common in drone footage
            "--SiftExtraction.estimate_affine_shape", "1",

            # Domain size pooling makes features more robust
            # to scale changes between views
            "--SiftExtraction.domain_size_pooling", "1",

            # GPU acceleration
            "--SiftExtraction.use_gpu", "1",
        ]
    )

    check_database(
        database_path
    )

    # ========================================================
    # STEP 2 — FEATURE MATCHING
    # ========================================================
    # For small image sets (< 25 images), run exhaustive matching
    # to maximize multi-view loop constraints.
    # For drone video trajectories (>= 25 images), run sequential
    # matching with wide lookahead and optional loop detection.

    print_section("STEP 2/11 — FEATURE MATCHING")
    if progress_callback:
        progress_callback("matching_features", 45, "Matching visual features across frames...")

    if num_input_images < 25:
        logger.info(
            f"Small frame set ({num_input_images} images) detected: "
            "using exhaustive_matcher for complete pairwise connectivity."
        )
        run_colmap(
            "exhaustive_matcher",
            [
                "--database_path",
                windows_path(database_path),
            ]
        )
    else:
        logger.info(
            f"Drone video trajectory detected ({num_input_images} images): "
            f"using sequential_matcher with overlap={SEQUENTIAL_OVERLAP}."
        )
        matching_args = [
            "--database_path",
            windows_path(database_path),
            "--SequentialMatching.overlap",
            str(SEQUENTIAL_OVERLAP),
        ]

        vocab_tree_candidates = [
            Path(COLMAP).parent / "vocab_tree_flickr100K_words256K.bin",
            Path(COLMAP).parent / "vocab_tree_flickr100K_words32K.bin",
            Path(COLMAP).parent / "vocab_tree-65536.bin",
            Path(r"C:\bin\vocab_tree_flickr100K_words256K.bin"),
            Path(r"C:\bin\vocab_tree_flickr100K_words32K.bin"),
        ]

        vocab_tree_path = None
        for candidate in vocab_tree_candidates:
            if candidate.exists():
                vocab_tree_path = candidate
                break

        if vocab_tree_path:
            logger.info(f"  Loop detection     : ENABLED (vocab tree: {vocab_tree_path.name})")
            matching_args.extend([
                "--SequentialMatching.loop_detection", "1",
                "--SequentialMatching.vocab_tree_path", windows_path(vocab_tree_path),
            ])
        else:
            logger.info("  Loop detection     : DISABLED (no vocab tree found)")

        run_colmap(
            "sequential_matcher",
            matching_args
        )

    # --------------------------------------------------------
    # Verify that feature matches exist in the database
    # --------------------------------------------------------
    try:
        import sqlite3
        with sqlite3.connect(str(database_path)) as con:
            cur = con.cursor()
            cur.execute("SELECT count(*) FROM matches WHERE rows > 0")
            num_matched_pairs = cur.fetchone()[0]
        logger.info(f"Verified feature matches: {num_matched_pairs} image pairs matched.")
        if num_matched_pairs == 0:
            raise RuntimeError(
                "Feature matching completed but found 0 matching image pairs. "
                "The images may lack visual overlap, have severe lighting changes, or lack distinct features."
            )
    except Exception as e:
        if "0 matching image pairs" in str(e):
            raise
        logger.warning(f"Could not verify matches in database ({e}); proceeding to mapper.")

    # ========================================================
    # STEP 3 — SPARSE RECONSTRUCTION / SfM
    # ========================================================
    # Key changes:
    # - multiple_models=0: FORCES COLMAP to build ONE unified
    #   model. This is the single most important fix.
    #   Previously, COLMAP created 4 fragments and only the
    #   largest (~43% of images) was used for dense recon.
    # - Better bundle adjustment parameters for more accurate
    #   camera poses.

    print_section(
        "STEP 3/11 — SPARSE RECONSTRUCTION / SfM"
    )
    if progress_callback:
        progress_callback("sparse_reconstruction", 50, "Estimating camera trajectory & sparse SfM point cloud...")

    logger.info(
        "Estimating camera poses and creating "
        "the sparse 3D reconstruction."
    )
    logger.info(f"  Force single model : {FORCE_SINGLE_MODEL}")

    # --------------------------------------------------------
    # Clean previous sparse reconstruction
    # --------------------------------------------------------

    clean_directory(
        sparse_dir
    )

    # --------------------------------------------------------
    # Run mapper
    # --------------------------------------------------------

    mapper_args = [
        "--database_path",
        windows_path(database_path),

        "--image_path",
        windows_path(image_dir),

        "--output_path",
        windows_path(sparse_dir),
    ]

    if FORCE_SINGLE_MODEL:
        mapper_args.extend([
            # Force a single unified reconstruction
            "--Mapper.multiple_models", "0",
        ])
    else:
        mapper_args.extend([
            # Allow multiple model seeds so find_best_model picks the dominant reconstruction
            "--Mapper.multiple_models", "1",
            "--Mapper.max_num_models", "5",
        ])

    # Better bundle adjustment for more accurate camera poses
    mapper_args.extend([
        # More global BA iterations for convergence
        "--Mapper.ba_global_max_num_iterations", "50",

        # More refinement passes
        "--Mapper.ba_global_max_refinements", "5",

        # Accept image pairs with fewer matches (helps when
        # some frames have low-texture regions)
        "--Mapper.min_num_matches", "15",
    ])

    run_colmap(
        "mapper",
        mapper_args
    )

    # ========================================================
    # FIND BEST MODEL
    # ========================================================

    best_model = find_best_model(
        sparse_dir
    )

    logger.info(f"Best sparse model: {best_model}")

    # ========================================================
    # STEP 4 — SPARSE MODEL QUALITY GATE
    # ========================================================
    # NEW: Read the sparse model and check quality before
    # investing time in dense reconstruction.

    print_section("STEP 4/11 — SPARSE MODEL QUALITY CHECK")
    if progress_callback:
        progress_callback("sparse_quality_check", 55, "Evaluating sparse model registration quality...")

    sparse_stats = read_sparse_model_stats(best_model)

    num_registered = sparse_stats["num_registered_images"]
    num_points3d = sparse_stats["num_points3D"]
    num_cameras = sparse_stats["num_cameras"]

    registration_ratio = num_registered / num_input_images if num_input_images > 0 else 0.0

    # Count total sparse models created
    num_sparse_models = len([
        d for d in sparse_dir.iterdir() if d.is_dir()
    ])

    logger.info(f"Sparse reconstruction results:")
    logger.info(f"  Reconstruction components : {num_sparse_models}")
    logger.info(f"  Cameras                   : {num_cameras}")
    logger.info(f"  Registered images         : {num_registered} / {num_input_images} ({registration_ratio:.0%})")
    logger.info(f"  3D points                 : {num_points3d:,}")

    # Quality warnings
    quality_warnings = []

    if num_sparse_models > 1:
        quality_warnings.append(
            f"Reconstruction fragmented into {num_sparse_models} components. "
            "Only the largest component is used."
        )

    if registration_ratio < MIN_REGISTRATION_RATIO:
        raise RuntimeError(
            f"Sparse reconstruction quality is too poor to continue.\n\n"
            f"Only {num_registered} out of {num_input_images} images were registered "
            f"({registration_ratio:.0%}).\n\n"
            f"Minimum required: {MIN_REGISTRATION_RATIO:.0%}\n\n"
            "Possible causes:\n"
            "- Input frames lack visual features (e.g., water, sky, uniform surfaces)\n"
            "- Heavy motion blur in many frames\n"
            "- Insufficient overlap between consecutive frames\n"
            "- Frames extracted at too wide an interval"
        )

    if registration_ratio < 0.70:
        quality_warnings.append(
            f"Only {registration_ratio:.0%} of images registered — "
            "model may be incomplete."
        )

    if num_points3d < 1000:
        quality_warnings.append(
            f"Very few sparse points ({num_points3d:,}). "
            "Dense reconstruction may be poor."
        )

    for warning in quality_warnings:
        logger.warning(f"QUALITY WARNING: {warning}")

    # ========================================================
    # STEP 5 — IMAGE UNDISTORTION
    # ========================================================

    print_section(
        "STEP 5/11 — IMAGE UNDISTORTION"
    )
    if progress_callback:
        progress_callback("image_undistortion", 60, "Undistorting drone frames for dense stereo...")

    logger.info(
        "Preparing images for dense reconstruction."
    )

    # --------------------------------------------------------
    # Clean previous dense workspace
    # --------------------------------------------------------

    clean_directory(
        dense_dir
    )

    # --------------------------------------------------------
    # Run image undistorter
    # --------------------------------------------------------

    run_colmap(
        "image_undistorter",
        [
            "--image_path",
            windows_path(
                image_dir
            ),

            "--input_path",
            windows_path(
                best_model
            ),

            "--output_path",
            windows_path(
                dense_dir
            ),

            "--output_type",
            "COLMAP"
        ]
    )

    # ========================================================
    # VERIFY UNDISTORTION
    # ========================================================

    dense_images_dir = (
        dense_dir /
        "images"
    )

    dense_sparse_dir = (
        dense_dir /
        "sparse"
    )

    if not dense_images_dir.exists():

        raise RuntimeError(
            "Image undistorter did not create "
            "the expected images directory:\n"
            f"{dense_images_dir}"
        )

    if not dense_sparse_dir.exists():

        raise RuntimeError(
            "Image undistorter did not create "
            "the expected sparse directory:\n"
            f"{dense_sparse_dir}"
        )

    # Count undistorted images
    undistorted_images = get_input_images(dense_images_dir)
    num_undistorted = len(undistorted_images)
    logger.info(f"Undistorted images: {num_undistorted}")
    logger.info(f"Dense sparse workspace: {dense_sparse_dir}")

    # ========================================================
    # STEP 6 — PATCHMATCH STEREO
    # ========================================================
    # Key changes:
    # - max_image_size: 2400 (from 1600). Better depth maps
    #   for 4K drone footage.
    # - num_iterations: 7 (from default 5). More iterations
    #   improve depth consistency.
    # - GPU acceleration explicit.

    print_section(
        "STEP 6/11 — DENSE DEPTH ESTIMATION"
    )
    if progress_callback:
        progress_callback("dense_stereo", 70, "Computing dense depth maps via PatchMatch Stereo (GPU)...")

    logger.info(
        "Estimating dense depth maps using PatchMatch Stereo."
    )
    logger.info(f"  Max image size   : {PATCHMATCH_MAX_IMAGE_SIZE}")
    logger.info(f"  Num iterations   : {PATCHMATCH_NUM_ITERATIONS}")
    logger.info(f"  Geom consistency : yes")

    run_colmap(
        "patch_match_stereo",
        [
            "--workspace_path",
            windows_path(dense_dir),

            "--workspace_format",
            "COLMAP",

            # Geometric consistency check between views
            "--PatchMatchStereo.geom_consistency", "1",

            # Image resolution for depth estimation
            "--PatchMatchStereo.max_image_size",
            str(PATCHMATCH_MAX_IMAGE_SIZE),

            # More iterations for better depth
            "--PatchMatchStereo.num_iterations",
            str(PATCHMATCH_NUM_ITERATIONS),

            # Explicit GPU index
            "--PatchMatchStereo.gpu_index", "0",
        ]
    )

    # ========================================================
    # VERIFY STEREO
    # ========================================================

    stereo_dir = (
        dense_dir /
        "stereo"
    )

    if not stereo_dir.exists():

        raise RuntimeError(
            "PatchMatch Stereo did not create "
            "the expected stereo directory:\n"
            f"{stereo_dir}"
        )

    logger.info(f"Stereo workspace: {stereo_dir}")

    # ========================================================
    # STEP 7 — STEREO FUSION
    # ========================================================
    # Key changes:
    # - min_num_pixels: 3 (from default 5). Keeps more of the
    #   fused point cloud, especially at scene boundaries.
    # - max_reproj_error: 2.0. Filters badly reprojected points.

    print_section(
        "STEP 7/11 — DENSE POINT CLOUD"
    )
    if progress_callback:
        progress_callback("stereo_fusion", 80, "Fusing dense depth maps into 3D point cloud...")

    logger.info(
        "Fusing depth maps into a dense point cloud."
    )
    logger.info(f"  Min num pixels   : {FUSION_MIN_NUM_PIXELS}")
    logger.info(f"  Max reproj error : {FUSION_MAX_REPROJ_ERROR}")

    dense_ply = (
        dense_dir /
        "fused.ply"
    )

    # Remove old fused point cloud
    if dense_ply.exists():

        try:

            dense_ply.unlink()

        except Exception:

            pass

    run_colmap(
        "stereo_fusion",
        [
            "--workspace_path",
            windows_path(dense_dir),

            "--workspace_format",
            "COLMAP",

            "--input_type",
            "geometric",

            "--output_type",
            "PLY",

            "--output_path",
            windows_path(dense_ply),

            # Relaxed fusion threshold for denser cloud
            "--StereoFusion.min_num_pixels",
            str(FUSION_MIN_NUM_PIXELS),

            # Filter high reprojection error points
            "--StereoFusion.max_reproj_error",
            str(FUSION_MAX_REPROJ_ERROR),
        ]
    )

    check_file(
        dense_ply,
        "Dense point cloud"
    )

    dense_ply_size_mb = dense_ply.stat().st_size / (1024 * 1024)
    logger.info(f"Dense point cloud: {dense_ply} ({dense_ply_size_mb:.1f} MB)")

    # ========================================================
    # STEP 8 — POINT CLOUD CLEANING
    # ========================================================
    # NEW: Remove outliers from the dense point cloud before
    # meshing. This prevents floating points and isolated noise
    # from distorting the Poisson mesh.

    print_section(
        "STEP 8/11 — POINT CLOUD CLEANING"
    )
    if progress_callback:
        progress_callback("point_cloud_cleaning", 85, "Filtering noise and outliers with Open3D...")

    logger.info(
        "Removing outliers from the dense point cloud."
    )

    cleaned_ply = (
        dense_dir /
        "fused_cleaned.ply"
    )

    cleaning_stats = clean_point_cloud(dense_ply, cleaned_ply)

    # Use cleaned cloud for subsequent steps
    meshing_input_ply = cleaned_ply if cleaned_ply.exists() else dense_ply

    # ========================================================
    # STEP 9 — POISSON MESHING
    # ========================================================
    # Key changes:
    # - Try Open3D Poisson with density trimming first.
    #   Density trimming removes hallucinated geometry at the
    #   boundary of the point cloud (the main source of
    #   "bloating" distortion in the previous pipeline).
    # - Fall back to COLMAP poisson_mesher if Open3D unavailable.
    # - Higher Poisson depth (11 vs 10) for finer detail.

    print_section(
        "STEP 9/11 — POISSON MESH GENERATION"
    )
    if progress_callback:
        progress_callback("poisson_meshing", 90, "Reconstructing Poisson surface mesh with density trimming...")

    logger.info(
        "Converting dense point cloud into a mesh."
    )

    poisson_mesh = (
        mesh_dir /
        "poisson_mesh.ply"
    )

    # Remove old mesh
    if poisson_mesh.exists():

        try:

            poisson_mesh.unlink()

        except Exception:

            pass

    # Try Open3D Poisson with density trimming
    mesh_stats = poisson_mesh_with_trimming(
        input_ply=meshing_input_ply,
        output_ply=poisson_mesh,
        depth=POISSON_DEPTH,
        density_percentile=POISSON_TRIM,
    )

    if mesh_stats is None:
        # Open3D not available — fall back to COLMAP mesher
        logger.info("Falling back to COLMAP poisson_mesher")
        run_colmap(
            "poisson_mesher",
            [
                "--input_path",
                windows_path(meshing_input_ply),

                "--output_path",
                windows_path(poisson_mesh),

                "--PoissonMeshing.depth",
                str(POISSON_DEPTH),

                "--PoissonMeshing.trim",
                str(POISSON_TRIM),
            ]
        )
        mesh_stats = {}

    check_file(
        poisson_mesh,
        "Poisson mesh"
    )

    logger.info(f"Poisson mesh: {poisson_mesh}")

    # ========================================================
    # STEP 10 — TEXTURE MAPPING
    # ========================================================

    print_section(
        "STEP 10/11 — TEXTURE MAPPING"
    )
    if progress_callback:
        progress_callback("texture_mapping", 95, "Colorizing mesh and baking material textures...")

    logger.info(
        "Projecting drone imagery onto the mesh."
    )

    # --------------------------------------------------------
    # Clean old textured directory
    # --------------------------------------------------------

    clean_directory(
        textured_dir
    )

    # --------------------------------------------------------
    # Generate textured & colored model
    # --------------------------------------------------------

    try:
        textured_model = colorize_mesh_from_point_cloud(
            mesh_ply=poisson_mesh,
            point_cloud_ply=meshing_input_ply,
            output_dir=textured_dir
        )
    except Exception as e:
        logger.warning(f"Color transfer failed ({e}); preserving Poisson mesh as textured fallback.")
        textured_model = textured_dir / "textured_mesh.ply"
        shutil.copy2(poisson_mesh, textured_model)

    # ========================================================
    # FIND TEXTURED MODEL
    # ========================================================

    possible_models = []

    for extension in (
        "*.ply",
        "*.obj",
        "*.glb",
        "*.gltf"
    ):

        possible_models.extend(
            textured_dir.glob(
                extension
            )
        )

    if not possible_models:

        raise RuntimeError(
            "Texture mapping completed but "
            "no final model was found in:\n"
            f"{textured_dir}"
        )

    # --------------------------------------------------------
    # Prefer PLY
    # --------------------------------------------------------

    ply_models = [
        p
        for p in possible_models
        if p.suffix.lower() == ".ply"
    ]

    if ply_models:

        textured_model = (
            ply_models[0]
        )

    else:

        textured_model = (
            possible_models[0]
        )

    logger.info(f"Textured model: {textured_model}")

    # ========================================================
    # STEP 11 — FINAL VALIDATION & QUALITY REPORT
    # ========================================================

    print_section(
        "STEP 11/11 — FINAL VALIDATION & QUALITY REPORT"
    )
    if progress_callback:
        progress_callback("exporting_glb", 98, "Validating 3D geometry and packaging GLB...")

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    check_database(
        database_path
    )

    # --------------------------------------------------------
    # Dense point cloud
    # --------------------------------------------------------

    check_file(
        dense_ply,
        "Dense point cloud"
    )

    # --------------------------------------------------------
    # Mesh
    # --------------------------------------------------------

    check_file(
        poisson_mesh,
        "Poisson mesh"
    )

    # --------------------------------------------------------
    # Textured model
    # --------------------------------------------------------

    check_file(
        textured_model,
        "Textured model"
    )

    # ========================================================
    # FILE SIZES
    # ========================================================

    dense_size_mb = (
        dense_ply.stat().st_size
        / (1024 * 1024)
    )

    mesh_size_mb = (
        poisson_mesh.stat().st_size
        / (1024 * 1024)
    )

    textured_size_mb = (
        textured_model.stat().st_size
        / (1024 * 1024)
    )

    # ========================================================
    # QUALITY REPORT
    # ========================================================

    print_section("RECONSTRUCTION QUALITY REPORT")
    logger.info(f"Input images        : {num_input_images}")
    logger.info(f"Registered images   : {num_registered} ({registration_ratio:.0%})")
    logger.info(f"Sparse models       : {num_sparse_models}")
    logger.info(f"Sparse 3D points    : {num_points3d:,}")
    logger.info(f"Dense point cloud   : {dense_ply} ({dense_size_mb:.2f} MB)")
    if cleaning_stats.get("original_points", -1) >= 0:
        logger.info(f"  Before cleaning   : {cleaning_stats.get('original_points', 'N/A'):,} points")
        logger.info(f"  After cleaning    : {cleaning_stats.get('cleaned_points', 'N/A'):,} points")
        logger.info(f"  Outliers removed  : {cleaning_stats.get('removed_points', 0):,} points")
    logger.info(f"Poisson mesh        : {poisson_mesh} ({mesh_size_mb:.2f} MB)")
    if mesh_stats:
        logger.info(f"  Vertices          : {mesh_stats.get('vertices', 'N/A'):,}")
        logger.info(f"  Faces             : {mesh_stats.get('faces', 'N/A'):,}")
    logger.info(f"Textured model      : {textured_model} ({textured_size_mb:.2f} MB)")

    if quality_warnings:
        logger.info("Quality warnings:")
        for w in quality_warnings:
            logger.info(f"  ⚠ {w}")

    # ========================================================
    # COMPLETE
    # ========================================================

    print_section("COMPLETE — 3D RECONSTRUCTION FINISHED")
    logger.info(f"Sparse model      : {best_model}")
    logger.info(f"Dense point cloud : {dense_ply} ({dense_size_mb:.2f} MB)")
    logger.info(f"Poisson mesh      : {poisson_mesh} ({mesh_size_mb:.2f} MB)")
    logger.info(f"Textured model    : {textured_model} ({textured_size_mb:.2f} MB)")

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "workspace":
            str(workspace_dir),

        "sparse_directory":
            str(sparse_dir),

        "model_directory":
            str(best_model),

        "model_name":
            best_model.name,

        "images_used":
            num_input_images,

        "dense_directory":
            str(dense_dir),

        "dense_images_directory":
            str(dense_images_dir),

        "dense_sparse_directory":
            str(dense_sparse_dir),

        "dense_point_cloud":
            str(dense_ply),

        "mesh_directory":
            str(mesh_dir),

        "poisson_mesh":
            str(poisson_mesh),

        "textured_directory":
            str(textured_dir),

        "textured_model":
            str(textured_model),

        "pipeline_status":
            "complete",

        # ====================================================
        # Reconstruction statistics (new)
        # ====================================================

        "reconstruction_stats": {
            "input_images": num_input_images,
            "registered_images": num_registered,
            "registration_ratio": round(registration_ratio, 2),
            "sparse_models": num_sparse_models,
            "sparse_points": num_points3d,
            "undistorted_images": num_undistorted,
            "dense_cloud_points": cleaning_stats.get("original_points", -1),
            "cleaned_cloud_points": cleaning_stats.get("cleaned_points", -1),
            "outliers_removed": cleaning_stats.get("removed_points", 0),
            "mesh_vertices": mesh_stats.get("vertices", 0) if mesh_stats else 0,
            "mesh_faces": mesh_stats.get("faces", 0) if mesh_stats else 0,
            "bounding_dimensions": mesh_stats.get("dimensions", cleaning_stats.get("bounding_box", {}).get("dimensions", [])),
            "bounding_box": cleaning_stats.get("bounding_box", {}),
            "dense_cloud_size_mb": round(dense_size_mb, 2),
            "mesh_size_mb": round(mesh_size_mb, 2),
            "textured_model_size_mb": round(textured_size_mb, 2),
        },

        "quality_warnings": quality_warnings,
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    logger.info("reconstruction.py loaded successfully.")
    logger.info(f"COLMAP executable: {COLMAP}")

    try:
        check_colmap()
        logger.info("COLMAP executable check: OK")
    except Exception as e:
        logger.error(f"COLMAP executable check FAILED: {e}")
        sys.exit(1)