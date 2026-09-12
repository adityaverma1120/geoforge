import open3d as o3d

mesh_path = r"C:\Users\Aditya verma\Desktop\Drone3DProject\colmap_workspace\dense\meshed-poisson.ply"

print("Loading mesh...")

mesh = o3d.io.read_triangle_mesh(mesh_path)

if mesh.is_empty():
    print("ERROR: Mesh is empty.")
    exit()

print(f"Vertices: {len(mesh.vertices)}")
print(f"Triangles: {len(mesh.triangles)}")

print("Opening mesh viewer...")

o3d.visualization.draw_geometries(
    [mesh],
    window_name="University 3D Mesh",
    width=1280,
    height=720
)