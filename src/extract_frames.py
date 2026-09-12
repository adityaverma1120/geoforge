import cv2
import os

video_path = "../input/drone_video.mp4"
output_folder = "../frames"

# Check whether the video file exists
if not os.path.exists(video_path):
    print("ERROR: Video file not found!")
    print("Looking for:", os.path.abspath(video_path))
    exit()

os.makedirs(output_folder, exist_ok=True)

video = cv2.VideoCapture(video_path)

# Check whether OpenCV opened the video
if not video.isOpened():
    print("ERROR: OpenCV could not open the video.")
    exit()

frame_count = 0

while True:
    success, frame = video.read()

    if not success:
        break

    frame_name = os.path.join(
        output_folder,
        f"frame_{frame_count:05d}.jpg"
    )

    cv2.imwrite(frame_name, frame)

    frame_count += 1

video.release()

print(f"Finished! Extracted {frame_count} frames.")