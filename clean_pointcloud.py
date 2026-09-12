import open3d as o3d

input_path = r"C:\Users\Aditya verma\Desktop\Drone3DProject\colmap_workspace\dense\fused.ply"

output_path = r"C:\Users\Aditya verma\Desktop\Drone3DProject\colmap_workspace\dense\cleaned_pointcloud.ply"

print("Loading point cloud...")

pcd = o3d.io.read_point_cloud(input_path)

print(f"Original points: {len(pcd.points)}")

if pcd.is_empty():
    print("ERROR: Point cloud is empty.")
    exit()

# Downsample the point cloud
print("Downsampling...")

pcd = pcd.voxel_down_sample(voxel_size=0.03)

print(f"After downsampling: {len(pcd.points)}")

# Remove statistical outliers
print("Removing noise...")

pcd_clean, ind = pcd.remove_statistical_outlier(
    nb_neighbors=20,
    std_ratio=2.0
)

print(f"After noise removal: {len(pcd_clean.points)}")

# Save cleaned point cloud
o3d.io.write_point_cloud(output_path, pcd_clean)

print("Clean point cloud saved:")
print(output_path)

# Display
print("Opening cleaned point cloud...")

o3d.visualization.draw_geometries(
    [pcd_clean],
    window_name="Cleaned University Point Cloud",
    width=1280,
    height=720
)