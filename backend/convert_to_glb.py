"""
convert_to_glb.py

Converts a textured PLY mesh + texture image into a single GLB file
that can be served to a browser via Three.js or model-viewer.

Usage (as a module):
    from convert_to_glb import convert_to_glb
    convert_to_glb(ply_file, texture_file, glb_file)

Usage (standalone test):
    Set TEXTURED_DIR below and run:
    python convert_to_glb.py
"""

import logging
from pathlib import Path

import trimesh
from PIL import Image

logger = logging.getLogger(__name__)


# ============================================================
# CONVERT TO GLB
# ============================================================

def convert_to_glb(
    ply_file: Path,
    texture_file: Path,
    glb_file: Path
) -> Path:
    """
    Convert a textured PLY + texture PNG into a single GLB file.

    Args:
        ply_file:     Path to input PLY mesh.
        texture_file: Path to texture image (PNG or JPG).
        glb_file:     Destination path for the output GLB.

    Returns:
        Path to the created GLB file.

    Raises:
        RuntimeError on any failure.
    """

    logger.info("=" * 70)
    logger.info("PLY + TEXTURE -> GLB")
    logger.info("=" * 70)
    logger.info(f"PLY file     : {ply_file}")
    logger.info(f"Texture file : {texture_file}")
    logger.info(f"GLB output   : {glb_file}")

    # ========================================================
    # CHECK INPUT FILES
    # ========================================================

    if not ply_file.exists():
        raise RuntimeError(f"PLY mesh was not found:\n{ply_file}")

    if ply_file.stat().st_size == 0:
        raise RuntimeError(f"PLY mesh exists but is empty:\n{ply_file}")

    if not texture_file.exists():
        raise RuntimeError(f"Texture file was not found:\n{texture_file}")

    if texture_file.stat().st_size == 0:
        raise RuntimeError(f"Texture file exists but is empty:\n{texture_file}")

    # ========================================================
    # LOAD PLY
    # ========================================================

    logger.info("Loading PLY mesh...")

    try:
        mesh = trimesh.load(ply_file, force="mesh", process=False)
    except Exception as e:
        raise RuntimeError(f"Failed to load PLY mesh:\n{e}") from e

    logger.info(f"Loaded object type: {type(mesh)}")

    # ========================================================
    # HANDLE SCENE
    # ========================================================

    if isinstance(mesh, trimesh.Scene):
        logger.info("PLY contains a scene — concatenating geometry.")
        meshes = [
            g for g in mesh.geometry.values()
            if isinstance(g, trimesh.Trimesh)
        ]
        if not meshes:
            raise RuntimeError("No valid mesh geometry found inside the PLY.")
        mesh = trimesh.util.concatenate(meshes)

    # ========================================================
    # VERIFY MESH
    # ========================================================

    if not isinstance(mesh, trimesh.Trimesh):
        raise RuntimeError("PLY could not be loaded as a valid mesh.")

    if len(mesh.vertices) == 0:
        raise RuntimeError("PLY mesh contains no vertices.")

    if len(mesh.faces) == 0:
        raise RuntimeError("PLY mesh contains no faces.")

    logger.info(f"Vertices : {len(mesh.vertices):,}")
    logger.info(f"Faces    : {len(mesh.faces):,}")

    # ========================================================
    # CHECK UV COORDINATES
    # ========================================================

    try:
        uv = mesh.visual.uv
    except Exception:
        uv = None

    if uv is not None:
        logger.info(f"UV coordinates found: {len(uv):,}")
    else:
        logger.warning("No UV coordinates found — texture may not appear correctly.")

    # ========================================================
    # LOAD TEXTURE
    # ========================================================

    logger.info("Loading texture...")

    try:
        texture = Image.open(texture_file)
        texture.load()
    except Exception as e:
        raise RuntimeError(f"Could not load texture:\n{e}") from e

    logger.info(f"Texture size : {texture.size[0]} x {texture.size[1]}")
    logger.info(f"Texture mode : {texture.mode}")

    # ========================================================
    # APPLY TEXTURE
    # ========================================================

    if uv is not None:
        try:
            material = trimesh.visual.material.PBRMaterial(
                baseColorTexture=texture
            )
            mesh.visual = trimesh.visual.TextureVisuals(
                uv=uv,
                image=texture,
                material=material
            )
            logger.info("Texture material attached.")
        except Exception as e:
            raise RuntimeError(f"Failed to attach texture to mesh:\n{e}") from e
    else:
        logger.warning("Exporting geometry without UV texture mapping.")

    # ========================================================
    # CREATE OUTPUT DIRECTORY
    # ========================================================

    glb_file.parent.mkdir(parents=True, exist_ok=True)

    if glb_file.exists():
        try:
            glb_file.unlink()
        except Exception as e:
            raise RuntimeError(
                f"Could not remove previous GLB:\n{glb_file}\n\nError: {e}"
            ) from e

    # ========================================================
    # EXPORT GLB
    # ========================================================

    logger.info("Exporting GLB...")

    try:
        mesh.export(glb_file, file_type="glb")
    except Exception as e:
        raise RuntimeError(f"GLB export failed:\n{e}") from e

    # ========================================================
    # VERIFY GLB
    # ========================================================

    if not glb_file.exists():
        raise RuntimeError("GLB file was not created.")

    if glb_file.stat().st_size == 0:
        raise RuntimeError("GLB file was created but is empty.")

    glb_size_mb = glb_file.stat().st_size / (1024 * 1024)

    logger.info("=" * 70)
    logger.info("GLB CONVERSION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"GLB file : {glb_file}")
    logger.info(f"GLB size : {glb_size_mb:.2f} MB")

    return glb_file


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    # --------------------------------------------------------
    # Edit TEXTURED_DIR to point at a job's textured folder.
    # --------------------------------------------------------
    TEXTURED_DIR = Path(
        r"C:\Users\Aditya verma\Desktop\Drone3DProject\backend\temp\<job_id>\colmap\textured"
    )

    ply_files = list(TEXTURED_DIR.glob("*.ply"))
    texture_files = list(TEXTURED_DIR.glob("*.png")) + list(TEXTURED_DIR.glob("*.jpg"))
    glb_out = TEXTURED_DIR / "model.glb"

    if not ply_files:
        print(f"ERROR: No PLY file found in {TEXTURED_DIR}")
        sys.exit(1)

    if not texture_files:
        print(f"ERROR: No texture file found in {TEXTURED_DIR}")
        sys.exit(1)

    convert_to_glb(
        ply_file=ply_files[0],
        texture_file=texture_files[0],
        glb_file=glb_out
    )

    print(f"\nDone! GLB written to: {glb_out}")
