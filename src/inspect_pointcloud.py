import open3d as o3d

ply_path = r"C:\Users\Aditya verma\Desktop\Drone3DProject\colmap_workspace\dense\fused.ply"

print("Loading point cloud...")

pcd = o3d.io.read_point_cloud(ply_path)

if pcd.is_empty():
    print("ERROR: Point cloud is empty.")
    exit()

print(f"Number of points: {len(pcd.points)}")

print("Opening 3D viewer...")

o3d.visualization.draw_geometries(
    [pcd],
    window_name="University Drone 3D Reconstruction",
    width=1280,
    height=720
)

print("Viewer closed.")