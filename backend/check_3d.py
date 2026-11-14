from pathlib import Path
import trimesh


# ============================================================
# PATHS
# ============================================================

# Dense fused point cloud
FUSED_PLY = Path(
    r"C:\Users\Aditya verma\Desktop\Drone3DProject\backend\temp\a4944e0b-5263-4695-9e92-d844d701e421\colmap\dense\fused.ply"
)

# Poisson mesh
MESH_PLY = Path(
    r"C:\Users\Aditya verma\Desktop\Drone3DProject\backend\temp\a4944e0b-5263-4695-9e92-d844d701e421\colmap\mesh\poisson_mesh.ply"
)

# Final GLB model used by the web viewer
GLB_FILE = Path(
    r"C:\Users\Aditya verma\Desktop\Drone3DProject\backend\temp\a4944e0b-5263-4695-9e92-d844d701e421\colmap\textured\model.glb"
)


# ============================================================
# PRINT SECTION
# ============================================================

def print_section(title):

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


# ============================================================
# INSPECT MESH
# ============================================================

def inspect_mesh(mesh):

    print()
    print("Vertices:")
    print(
        f"{len(mesh.vertices):,}"
    )

    print()
    print("Faces:")
    print(
        f"{len(mesh.faces):,}"
    )

    # --------------------------------------------------------
    # BOUNDS
    # --------------------------------------------------------

    try:

        bounds = mesh.bounds

        minimum = bounds[0]
        maximum = bounds[1]

        size = maximum - minimum

        print()
        print("MIN:")
        print(minimum)

        print()
        print("MAX:")
        print(maximum)

        print()
        print("DIMENSIONS:")

        print(
            f"X = {size[0]:.6f}"
        )

        print(
            f"Y = {size[1]:.6f}"
        )

        print(
            f"Z = {size[2]:.6f}"
        )

        # ----------------------------------------------------
        # EXTENT RATIO
        # ----------------------------------------------------

        largest = max(size)
        smallest = min(size)

        print()
        print("FLATNESS RATIO:")

        if largest > 0:

            ratio = smallest / largest

            print(
                f"{ratio:.6f}"
            )

        else:

            print(
                "0.000000"
            )

        print()
        print("EXTENT RATIO:")

        if largest > 0:

            print(
                f"Smallest dimension / "
                f"Largest dimension = "
                f"{smallest / largest:.6f}"
            )

        else:

            print(
                "Cannot calculate."
            )

    except Exception as e:

        print()
        print(
            f"Could not calculate bounds: {e}"
        )

    # --------------------------------------------------------
    # MESH QUALITY
    # --------------------------------------------------------

    print()
    print("MESH QUALITY:")

    try:

        print(
            f"Watertight : "
            f"{mesh.is_watertight}"
        )

    except Exception as e:

        print(
            f"Watertight : Could not calculate ({e})"
        )

    try:

        print(
            f"Convex     : "
            f"{mesh.is_convex}"
        )

    except Exception as e:

        print(
            f"Convex     : Could not calculate ({e})"
        )

    try:

        print(
            f"Winding consistent : "
            f"{mesh.is_winding_consistent}"
        )

    except Exception as e:

        print(
            f"Winding consistent : Could not calculate ({e})"
        )

    # IMPORTANT:
    # Do NOT use mesh.faces_sparse here.
    # It requires scipy and is unnecessary for this diagnostic.


# ============================================================
# INSPECT POINT CLOUD
# ============================================================

def inspect_point_cloud(point_cloud):

    print()
    print("POINT CLOUD INFORMATION:")

    try:

        points = point_cloud.vertices

        print()
        print(
            f"Points : {len(points):,}"
        )

        if len(points) == 0:

            print()
            print(
                "WARNING: Point cloud contains no points."
            )

            return False

        # ----------------------------------------------------
        # BOUNDS
        # ----------------------------------------------------

        bounds = point_cloud.bounds

        minimum = bounds[0]
        maximum = bounds[1]

        size = maximum - minimum

        print()
        print("MIN:")
        print(minimum)

        print()
        print("MAX:")
        print(maximum)

        print()
        print("DIMENSIONS:")

        print(
            f"X = {size[0]:.6f}"
        )

        print(
            f"Y = {size[1]:.6f}"
        )

        print(
            f"Z = {size[2]:.6f}"
        )

        largest = max(size)
        smallest = min(size)

        print()
        print("EXTENT RATIO:")

        if largest > 0:

            print(
                f"Smallest dimension / "
                f"Largest dimension = "
                f"{smallest / largest:.6f}"
            )

        else:

            print(
                "Cannot calculate."
            )

        return True

    except Exception as e:

        print()
        print(
            f"Point cloud inspection error: {e}"
        )

        return False


# ============================================================
# INSPECT UV / TEXTURE
# ============================================================

def inspect_visuals(mesh):

    print()
    print("VISUAL / TEXTURE INFORMATION:")

    try:

        visual = mesh.visual

        # ----------------------------------------------------
        # UV
        # ----------------------------------------------------

        if (
            hasattr(
                visual,
                "uv"
            )
            and
            visual.uv is not None
        ):

            print(
                "UV coordinates : FOUND"
            )

            print(
                f"UV count       : "
                f"{len(visual.uv):,}"
            )

        else:

            print(
                "UV coordinates : NOT FOUND"
            )

        # ----------------------------------------------------
        # MATERIAL
        # ----------------------------------------------------

        material = None

        if hasattr(
            visual,
            "material"
        ):

            material = visual.material

        if material is not None:

            print(
                "Material       : FOUND"
            )

            print(
                f"Material type  : "
                f"{type(material)}"
            )

        else:

            print(
                "Material       : NOT FOUND"
            )

        # ----------------------------------------------------
        # TEXTURE IMAGE
        # ----------------------------------------------------

        texture_found = False

        # Check material image
        if material is not None:

            if hasattr(
                material,
                "image"
            ):

                image = material.image

                if image is not None:

                    texture_found = True

                    print(
                        "Texture image  : FOUND"
                    )

                    if hasattr(
                        image,
                        "size"
                    ):

                        print(
                            f"Texture size   : "
                            f"{image.size[0]} x "
                            f"{image.size[1]}"
                        )

            # Check base color texture
            if hasattr(
                material,
                "baseColorTexture"
            ):

                base_texture = (
                    material.baseColorTexture
                )

                if base_texture is not None:

                    texture_found = True

                    print(
                        "Base color texture : FOUND"
                    )

        # Check visual image
        if (
            not texture_found
            and
            hasattr(
                visual,
                "image"
            )
        ):

            image = visual.image

            if image is not None:

                texture_found = True

                print(
                    "Texture image  : FOUND"
                )

                if hasattr(
                    image,
                    "size"
                ):

                    print(
                        f"Texture size   : "
                        f"{image.size[0]} x "
                        f"{image.size[1]}"
                    )

        if not texture_found:

            print(
                "Texture image  : NOT FOUND / NOT CONFIRMED"
            )

        return True

    except Exception as e:

        print(
            f"Visual inspection warning: {e}"
        )

        return False


# ============================================================
# INSPECT PLY
# ============================================================

def inspect_file(path, name):

    print_section(name)

    print()
    print("File:")
    print(path)

    # --------------------------------------------------------
    # CHECK EXISTENCE
    # --------------------------------------------------------

    if not path.exists():

        print()
        print("FILE DOES NOT EXIST")

        return False

    # --------------------------------------------------------
    # FILE SIZE
    # --------------------------------------------------------

    size_mb = (
        path.stat().st_size
        /
        (1024 * 1024)
    )

    print()
    print("Size:")

    print(
        f"{size_mb:.2f} MB"
    )

    # --------------------------------------------------------
    # LOAD FILE
    # --------------------------------------------------------

    print()
    print("Loading...")

    try:

        obj = trimesh.load(
            path,
            process=False
        )

    except Exception as e:

        print()
        print("ERROR:")

        print(e)

        return False

    # --------------------------------------------------------
    # OBJECT TYPE
    # --------------------------------------------------------

    print()
    print("Object type:")

    print(
        type(obj)
    )

    # ========================================================
    # POINT CLOUD
    # ========================================================

    if isinstance(
        obj,
        trimesh.points.PointCloud
    ):

        return inspect_point_cloud(
            obj
        )

    # ========================================================
    # SCENE
    # ========================================================

    if isinstance(
        obj,
        trimesh.Scene
    ):

        print()
        print("Scene geometries:")

        if not obj.geometry:

            print(
                "WARNING: Scene contains no geometry."
            )

            return False

        valid_geometry = False

        for name2, geometry in obj.geometry.items():

            print()
            print(
                f"Geometry: {name2}"
            )

            print(
                f"Type: {type(geometry)}"
            )

            if isinstance(
                geometry,
                trimesh.Trimesh
            ):

                valid_geometry = True

                inspect_mesh(
                    geometry
                )

                inspect_visuals(
                    geometry
                )

        return valid_geometry

    # ========================================================
    # TRIMESH
    # ========================================================

    if isinstance(
        obj,
        trimesh.Trimesh
    ):

        inspect_mesh(
            obj
        )

        inspect_visuals(
            obj
        )

        return True

    # ========================================================
    # UNKNOWN
    # ========================================================

    print()
    print(
        "WARNING: File did not load as a "
        "supported Trimesh object."
    )

    return False


# ============================================================
# INSPECT GLB
# ============================================================

def inspect_glb(path):

    print_section(
        "FINAL GLB MODEL CHECK"
    )

    print()
    print("GLB:")

    print(
        path
    )

    # --------------------------------------------------------
    # EXISTENCE
    # --------------------------------------------------------

    if not path.exists():

        print()
        print(
            "GLB FILE DOES NOT EXIST"
        )

        return False

    # --------------------------------------------------------
    # SIZE
    # --------------------------------------------------------

    size_mb = (
        path.stat().st_size
        /
        (1024 * 1024)
    )

    print()
    print(
        f"GLB size: {size_mb:.2f} MB"
    )

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    print()
    print(
        "Loading GLB..."
    )

    try:

        scene = trimesh.load(
            path,
            force="scene",
            process=False
        )

    except Exception as e:

        print()
        print(
            "GLB LOAD ERROR:"
        )

        print(
            e
        )

        return False

    print()
    print(
        "GLB object type:"
    )

    print(
        type(scene)
    )

    # --------------------------------------------------------
    # SCENE CHECK
    # --------------------------------------------------------

    if not isinstance(
        scene,
        trimesh.Scene
    ):

        print()
        print(
            "WARNING: GLB did not load as a Scene."
        )

        return False

    # --------------------------------------------------------
    # GEOMETRY COUNT
    # --------------------------------------------------------

    geometry_count = len(
        scene.geometry
    )

    print()
    print(
        f"Geometry objects: "
        f"{geometry_count}"
    )

    if geometry_count == 0:

        print()
        print(
            "ERROR: GLB contains no geometry."
        )

        return False

    # --------------------------------------------------------
    # TOTALS
    # --------------------------------------------------------

    total_vertices = 0
    total_faces = 0

    uv_objects = 0
    textured_objects = 0

    print()
    print(
        "GLB GEOMETRIES:"
    )

    for name, geometry in scene.geometry.items():

        print()
        print(
            f"Geometry: {name}"
        )

        print(
            f"Type: {type(geometry)}"
        )

        if not isinstance(
            geometry,
            trimesh.Trimesh
        ):

            continue

        vertices = len(
            geometry.vertices
        )

        faces = len(
            geometry.faces
        )

        total_vertices += vertices
        total_faces += faces

        print(
            f"Vertices: {vertices:,}"
        )

        print(
            f"Faces: {faces:,}"
        )

        # ----------------------------------------------------
        # UV
        # ----------------------------------------------------

        if (
            hasattr(
                geometry.visual,
                "uv"
            )
            and
            geometry.visual.uv is not None
        ):

            uv_objects += 1

            print(
                "UV: FOUND"
            )

        else:

            print(
                "UV: NOT FOUND"
            )

        # ----------------------------------------------------
        # MATERIAL
        # ----------------------------------------------------

        try:

            material = (
                geometry.visual.material
            )

            if material is not None:

                print(
                    "Material: FOUND"
                )

                texture_found = False

                # --------------------------------------------
                # IMAGE
                # --------------------------------------------

                if hasattr(
                    material,
                    "image"
                ):

                    if material.image is not None:

                        texture_found = True

                # --------------------------------------------
                # BASE COLOR TEXTURE
                # --------------------------------------------

                if hasattr(
                    material,
                    "baseColorTexture"
                ):

                    if (
                        material.baseColorTexture
                        is not None
                    ):

                        texture_found = True

                if texture_found:

                    textured_objects += 1

                    print(
                        "Texture: FOUND"
                    )

                else:

                    print(
                        "Texture: NOT CONFIRMED"
                    )

            else:

                print(
                    "Material: NOT FOUND"
                )

        except Exception as e:

            print(
                f"Material check warning: {e}"
            )

    # ========================================================
    # GLB TOTALS
    # ========================================================

    print()
    print(
        "GLB TOTALS:"
    )

    print(
        f"Total vertices : "
        f"{total_vertices:,}"
    )

    print(
        f"Total faces    : "
        f"{total_faces:,}"
    )

    print(
        f"Objects with UV : "
        f"{uv_objects}"
    )

    print(
        f"Objects with texture : "
        f"{textured_objects}"
    )

    # ========================================================
    # GLB BOUNDS
    # ========================================================

    try:

        bounds = scene.bounds

        minimum = bounds[0]
        maximum = bounds[1]

        dimensions = (
            maximum - minimum
        )

        print()
        print(
            "GLB BOUNDS:"
        )

        print(
            f"MIN: {minimum}"
        )

        print(
            f"MAX: {maximum}"
        )

        print()
        print(
            "GLB DIMENSIONS:"
        )

        print(
            f"X = {dimensions[0]:.6f}"
        )

        print(
            f"Y = {dimensions[1]:.6f}"
        )

        print(
            f"Z = {dimensions[2]:.6f}"
        )

    except Exception as e:

        print(
            f"Could not calculate GLB bounds: {e}"
        )

    # ========================================================
    # GLB STATUS
    # ========================================================

    print()
    print(
        "GLB STATUS:"
    )

    if (
        geometry_count > 0
        and
        total_vertices > 0
        and
        total_faces > 0
    ):

        print(
            "GLB GEOMETRY: OK"
        )

    else:

        print(
            "GLB GEOMETRY: FAILED"
        )

    if uv_objects > 0:

        print(
            "GLB UV MAPPING: OK"
        )

    else:

        print(
            "GLB UV MAPPING: NOT FOUND"
        )

    if textured_objects > 0:

        print(
            "GLB TEXTURE: OK"
        )

    else:

        print(
            "GLB TEXTURE: NOT CONFIRMED"
        )

    # Geometry is the essential requirement.
    # Texture is reported separately because some
    # valid GLBs may intentionally contain no texture.

    return (
        geometry_count > 0
        and
        total_vertices > 0
        and
        total_faces > 0
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=" * 70
    )

    print(
        "DRONE 3D RECONSTRUCTION DIAGNOSTIC"
    )

    print(
        "=" * 70
    )

    print()
    print(
        "Checking reconstruction outputs..."
    )

    # ========================================================
    # 1. DENSE POINT CLOUD
    # ========================================================

    fused_ok = inspect_file(
        FUSED_PLY,
        "DENSE FUSED POINT CLOUD"
    )

    # ========================================================
    # 2. POISSON MESH
    # ========================================================

    mesh_ok = inspect_file(
        MESH_PLY,
        "POISSON MESH"
    )

    # ========================================================
    # 3. FINAL GLB
    # ========================================================

    glb_ok = inspect_glb(
        GLB_FILE
    )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print_section(
        "DIAGNOSTIC SUMMARY"
    )

    print()

    print(
        f"Dense point cloud : "
        f"{'OK' if fused_ok else 'FAILED'}"
    )

    print(
        f"Poisson mesh      : "
        f"{'OK' if mesh_ok else 'FAILED'}"
    )

    print(
        f"Final GLB         : "
        f"{'OK' if glb_ok else 'FAILED'}"
    )

    print()

    # ========================================================
    # OVERALL STATUS
    # ========================================================

    if (
        fused_ok
        and
        mesh_ok
        and
        glb_ok
    ):

        print(
            "OVERALL STATUS: SUCCESS"
        )

        print()

        print(
            "The reconstruction pipeline produced:"
        )

        print(
            "1. Dense point cloud"
        )

        print(
            "2. Poisson mesh"
        )

        print(
            "3. Final GLB model"
        )

        print()

        print(
            "The GLB is ready for the web viewer."
        )

    else:

        print(
            "OVERALL STATUS: CHECK FAILED OUTPUTS"
        )

    print()

    print(
        "=" * 70
    )

    print(
        "DIAGNOSTIC COMPLETE"
    )

    print(
        "=" * 70
    )

    print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
    