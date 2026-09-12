import cv2
import os

# Folder containing all extracted frames
input_folder = "../frames"

# Folder where sharp frames will be saved
output_folder = "../good_frames"

# Create the output folder if it does not exist
os.makedirs(output_folder, exist_ok=True)

# Blur threshold
# Frames with a score below this value will be considered blurry
blur_threshold = 300

total_frames = 0
sharp_frames = 0
blurry_frames = 0

# Go through every file in the frames folder
for filename in os.listdir(input_folder):

    # Process only JPG images
    if filename.endswith(".jpg"):

        total_frames += 1

        # Full path of the frame
        image_path = os.path.join(input_folder, filename)

        # Read the image
        image = cv2.imread(image_path)

        # Convert image to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Calculate sharpness score using Laplacian variance
        sharpness_score = cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()

        # Decide whether the frame is sharp or blurry
        if sharpness_score >= blur_threshold:

            # Save sharp frame
            output_path = os.path.join(
                output_folder,
                filename
            )

            cv2.imwrite(output_path, image)

            sharp_frames += 1

            print(
                f"{filename} | "
                f"Score: {sharpness_score:.2f} | KEEP"
            )

        else:
            blurry_frames += 1

            print(
                f"{filename} | "
                f"Score: {sharpness_score:.2f} | BLURRY"
            )

print("\n----- RESULTS -----")
print(f"Total frames: {total_frames}")
print(f"Sharp frames kept: {sharp_frames}")
print(f"Blurry frames removed: {blurry_frames}")