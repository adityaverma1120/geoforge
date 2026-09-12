import logging
import os
import struct
import subprocess
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


# ============================================================
# COLMAP CONFIGURATION
# ============================================================

# Read from environment variable; fall back to the default install location.
# To override: set COLMAP_EXE=C:\path\to\colmap.exe in your environment.
COLMAP = os.environ.get("COLMAP_EXE", r"C:\bin\colmap.exe")


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
# Drone imagery often has repetitive textures (roofs, foliage)
# that need more features for robust matching.
# Default COLMAP: 8192. Increased for aerial scenes.
MAX_NUM_FEATURES = 16384

# --- Feature Matching ---
# Sequential matching overlap: how many neighbouring frames
# to match each image against. Higher = more robust
# trajectory but slower. 15 is a good balance for ~2fps
# extraction from drone video.
SEQUENTIAL_OVERLAP = 15

# --- Mapper / SfM ---
# Force a single reconstruction model instead of allowing
# COLMAP to fragment into multiple disconnected components.
# This is the MOST IMPORTANT setting for fixing distortion
# caused by fragmented sparse reconstructions.
FORCE_SINGLE_MODEL = True

# Minimum fraction of input images that must be registered
# in the sparse model. Below this, the reconstruction is
# considered too poor to proceed with dense reconstruction.
MIN_REGISTRATION_RATIO = 0.30

# --- PatchMatch Stereo ---
# Maximum image dimension for dense stereo.
# Higher = better depth resolution but more VRAM.
# 2400 is a good balance for 4K drone footage on 6+ GB GPUs.
PATCHMATCH_MAX_IMAGE_SIZE = 2400

# Number of PatchMatch iterations.
# More iterations improve depth consistency.
PATCHMATCH_NUM_ITERATIONS = 7

# --- Stereo Fusion ---
# Minimum pixels that must agree on a depth for it to be fused.
# Lower = denser point cloud but potentially more noise.
FUSION_MIN_NUM_PIXELS = 3

# Maximum reprojection error for fused points (pixels).
FUSION_MAX_REPROJ_ERROR = 2.0

# --- Poisson Meshing ---
# Octree depth for Poisson reconstruction.
# Higher = finer surface detail, more memory.
POISSON_DEPTH = 11

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
    best_size = -1

    for model in models:

        images_bin = (
            model /
            "images.bin"
        )

        if images_bin.exists():
            size = images_bin.stat().st_size
            logger.info(f"Sparse model {model.name}: images.bin = {size} bytes")

            if size > best_size:

                best_size = size
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
    # Save cleaned cloud
    # --------------------------------------------------------
    logger.info(f"Saving cleaned point cloud: {output_ply}")
    o3d.io.write_point_cloud(str(output_ply), cleaned)

    return {
        "original_points": original_count,
        "cleaned_points": cleaned_count,
        "removed_points": removed,
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
    # Save
    # --------------------------------------------------------
    logger.info(f"Saving Poisson mesh: {output_ply}")
    o3d.io.write_triangle_mesh(str(output_ply), mesh)

    return {
        "vertices_before_trim": vertices_before,
        "faces_before_trim": faces_before,
        "vertices": vertices_after,
        "faces": faces_after,
        "density_percentile": density_percentile,
    }


# ============================================================
# RECONSTRUCTION PIPELINE
# ============================================================

def run_reconstruction(
    image_dir: str,
    workspace_dir: str
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
    # Key changes:
    # - overlap: 15 instead of 10. Wider look-ahead provides
    #   more image pairs, reducing risk of chain breaks.
    # - loop_detection: enabled. Detects when the drone
    #   revisits areas, creating cross-links that prevent
    #   the reconstruction from fragmenting.
    # - vocab_tree_path: used for loop detection if available.

    print_section("STEP 2/11 — FEATURE MATCHING (sequential)")

    logger.info(
        "Matching visual features between adjacent frames. "
        "Using sequential_matcher — optimal for drone video."
    )
    logger.info(f"  Sequential overlap : {SEQUENTIAL_OVERLAP}")

    matching_args = [
        "--database_path",
        windows_path(database_path),

        # Look N frames ahead/behind each frame
        "--SequentialMatching.overlap",
        str(SEQUENTIAL_OVERLAP),
    ]

    # --------------------------------------------------------
    # Loop detection (optional — requires vocab tree)
    # --------------------------------------------------------
    # COLMAP's vocab tree enables loop closure detection:
    # when the drone flies back over previously seen areas,
    # it creates matches that stitch the reconstruction together.

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
        logger.info("  To enable, place a vocab tree binary next to colmap.exe")

    run_colmap(
        "sequential_matcher",
        matching_args
    )

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
    # Run mesh texturer
    # --------------------------------------------------------

    run_colmap(
        "mesh_texturer",
        [
            "--workspace_path",
            windows_path(
                dense_dir
            ),

            "--input_path",
            windows_path(
                poisson_mesh
            ),

            "--output_path",
            windows_path(
                textured_dir
            )
        ]
    )

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