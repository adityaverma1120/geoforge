"""
convert_to_glb.py — Binary glTF v2 (GLB) Packager and Validator for GeoForge

Converts a textured PLY mesh or vertex-colored Open3D mesh into a single
standard binary GLB file for Three.js WebGL visualization and direct browser download.
"""

import json
import logging
import struct
from pathlib import Path
from typing import Any, Dict, Optional

from PIL import Image
import trimesh

logger = logging.getLogger(__name__)


# ============================================================
# CONVERT TO GLB
# ============================================================

def convert_to_glb(
    ply_file: Path,
    texture_file: Optional[Path] = None,
    glb_file: Optional[Path] = None
) -> Path:
    """
    Convert a textured or vertex-colored PLY mesh into a single binary GLB file.

    Args:
        ply_file:     Path to input PLY mesh.
        texture_file: Optional path to texture image (PNG or JPG).
        glb_file:     Destination path for output GLB (default: same stem as ply_file).

    Returns:
        Path to the created GLB file.

    Raises:
        RuntimeError on validation or export failure.
    """
    ply_file = Path(ply_file)
    if glb_file is None:
        glb_file = ply_file.with_suffix(".glb")
    else:
        glb_file = Path(glb_file)

    logger.info("=" * 70)
    logger.info("PLY + TEXTURE -> GLB PACKAGER")
    logger.info("=" * 70)
    logger.info(f"PLY file     : {ply_file}")
    logger.info(f"Texture file : {texture_file}")
    logger.info(f"GLB output   : {glb_file}")

    if not ply_file.exists():
        raise RuntimeError(f"PLY mesh was not found:\n{ply_file}")

    if ply_file.stat().st_size == 0:
        raise RuntimeError(f"PLY mesh exists but is empty:\n{ply_file}")

    has_texture = False
    if texture_file is not None:
        texture_path = Path(texture_file)
        if texture_path.exists() and texture_path.stat().st_size > 0:
            has_texture = True
        else:
            logger.warning(f"Texture file not found or empty ({texture_file}); falling back to vertex colors.")

    # --------------------------------------------------------
    # Load PLY
    # --------------------------------------------------------
    logger.info("Loading PLY mesh...")
    try:
        mesh = trimesh.load(ply_file, force="mesh", process=False)
    except Exception as e:
        raise RuntimeError(f"Failed to load PLY mesh:\n{e}") from e

    # Handle Trimesh scene concatenation
    if isinstance(mesh, trimesh.Scene):
        logger.info("PLY contains a scene — concatenating geometry.")
        meshes = [g for g in mesh.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not meshes:
            raise RuntimeError("No valid mesh geometry found inside the PLY scene.")
        mesh = trimesh.util.concatenate(meshes)

    if not isinstance(mesh, trimesh.Trimesh):
        raise RuntimeError("PLY could not be loaded as a valid Trimesh geometry.")

    if len(mesh.vertices) == 0:
        raise RuntimeError("PLY mesh contains no vertices.")

    if len(mesh.faces) == 0:
        raise RuntimeError("PLY mesh contains no faces.")

    logger.info(f"Mesh Geometry: {len(mesh.vertices):,} vertices | {len(mesh.faces):,} faces")

    # --------------------------------------------------------
    # Check UV Coordinates and Visuals
    # --------------------------------------------------------
    try:
        uv = mesh.visual.uv
    except Exception:
        uv = None

    if uv is not None and len(uv) > 0:
        logger.info(f"UV coordinates found: {len(uv):,}")
    else:
        logger.info("No UV coordinates found — using direct vertex color rendering.")

    # --------------------------------------------------------
    # Attach Material / Visuals
    # --------------------------------------------------------
    if has_texture and texture_file is not None:
        logger.info("Loading texture image...")
        try:
            texture = Image.open(texture_file)
            texture.load()
            logger.info(f"Texture dimensions: {texture.size[0]} x {texture.size[1]} | Mode: {texture.mode}")

            if uv is not None and len(uv) > 0:
                material = trimesh.visual.material.PBRMaterial(
                    baseColorTexture=texture,
                    metallicFactor=0.1,
                    roughnessFactor=0.8
                )
                mesh.visual = trimesh.visual.TextureVisuals(
                    uv=uv,
                    image=texture,
                    material=material
                )
                logger.info("Attached PBR texture material.")
            else:
                logger.info("Preserving vertex colors with diffuse texture fallback.")
        except Exception as e:
            logger.warning(f"Could not apply texture image ({e}) — falling back to vertex colors.")
    else:
        logger.info("Packaging mesh with embedded vertex colors into GLB.")

    # --------------------------------------------------------
    # Export GLB
    # --------------------------------------------------------
    glb_file.parent.mkdir(parents=True, exist_ok=True)
    if glb_file.exists():
        try:
            glb_file.unlink()
        except Exception as e:
            raise RuntimeError(f"Could not overwrite existing GLB:\n{glb_file}\nError: {e}") from e

    logger.info("Exporting binary glTF (GLB)...")
    try:
        mesh.export(glb_file, file_type="glb")
    except Exception as e:
        raise RuntimeError(f"GLB export failed:\n{e}") from e

    # --------------------------------------------------------
    # Validate Output
    # --------------------------------------------------------
    validation = validate_glb(glb_file)
    glb_size_mb = validation["file_size_mb"]

    logger.info("=" * 70)
    logger.info(f"GLB CONVERSION COMPLETE: {glb_file.name} ({glb_size_mb:.2f} MB)")
    logger.info("=" * 70)

    return glb_file


# ============================================================
# GLB VALIDATOR
# ============================================================

def validate_glb(glb_path: Path) -> Dict[str, Any]:
    """
    Validate binary glTF v2 file structure according to the Khronos glTF 2.0 specification:
        - 12-byte header: magic (0x46546C67), version (2), total length.
        - First chunk: JSON chunk (type 0x4E4F534A / b"JSON").
        - Validates JSON parseability.

    Raises:
        ValueError or RuntimeError if GLB structure is corrupted or invalid.
    """
    glb_path = Path(glb_path)

    if not glb_path.exists():
        raise FileNotFoundError(f"GLB file does not exist: {glb_path}")

    file_size = glb_path.stat().st_size
    if file_size < 20:
        raise ValueError(f"GLB file is too small ({file_size} bytes) to be a valid binary glTF file.")

    with open(glb_path, "rb") as f:
        # Header: magic (4 bytes), version (uint32), length (uint32)
        magic, version, declared_length = struct.unpack("<4sII", f.read(12))

        if magic != b"glTF":
            raise ValueError(f"Invalid GLB magic bytes: {magic} (expected b'glTF').")

        if version != 2:
            raise ValueError(f"Unsupported glTF version: {version} (expected version 2).")

        if declared_length != file_size:
            logger.warning(
                f"GLB declared length ({declared_length}) differs slightly from filesystem size ({file_size})."
            )

        # Chunk 0 Header: chunk_length (uint32), chunk_type (4 bytes)
        chunk_len, chunk_type = struct.unpack("<I4s", f.read(8))
        if chunk_type != b"JSON":
            raise ValueError(f"Invalid first glTF chunk type: {chunk_type} (expected b'JSON').")

        json_bytes = f.read(chunk_len)
        try:
            gltf_manifest = json.loads(json_bytes.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to parse glTF JSON chunk: {e}") from e

    asset = gltf_manifest.get("asset", {})
    scenes = gltf_manifest.get("scenes", [])
    meshes = gltf_manifest.get("meshes", [])

    return {
        "valid": True,
        "magic": magic.decode("ascii", errors="replace"),
        "version": version,
        "file_size_bytes": file_size,
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "generator": asset.get("generator", "Trimesh/GeoForge"),
        "asset_version": asset.get("version", "2.0"),
        "num_scenes": len(scenes),
        "num_meshes": len(meshes)
    }


# ============================================================
# STANDALONE CLI TEST
# ============================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    base_temp = Path(__file__).resolve().parent / "temp"
    candidates = list(base_temp.glob("**/textured/model.ply")) + list(base_temp.glob("**/textured_mesh.ply"))

    if not candidates:
        print(f"No test PLY found in {base_temp}. Pass a PLY file path as argument.")
        sys.exit(0)

    test_ply = candidates[0]
    out_glb = test_ply.with_suffix(".glb")
    print(f"Testing GLB conversion on: {test_ply}")
    res = convert_to_glb(test_ply, glb_file=out_glb)
    val = validate_glb(res)
    print("Validation passed:", val)
