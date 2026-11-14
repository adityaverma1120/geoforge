import cv2
import os

# Folder containing sharp frames
input_folder = "../good_frames"

# Folder where selected frames will be saved
output_folder = "../selected_frames"

# Create output folder if it does not exist
os.makedirs(output_folder, exist_ok=True)

# Similarity threshold
similarity_threshold = 0.98

# Get all JPG files and sort them in frame order
files = sorted(
    [
        file
        for file in os.listdir(input_folder)
        if file.endswith(".jpg")
    ]
)

total_frames = len(files)
kept_frames = 0
redundant_frames = 0

# Store the previous frame that was kept
previous_frame = None

for filename in files:

    image_path = os.path.join(
        input_folder,
        filename
    )

    image = cv2.imread(image_path)

    # Convert image to grayscale
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # Resize image to make comparison faster
    gray = cv2.resize(
        gray,
        (320, 180)
    )

    # First frame is always kept
    if previous_frame is None:

        output_path = os.path.join(
            output_folder,
            filename
        )

        original_image = cv2.imread(image_path)

        cv2.imwrite(
            output_path,
            original_image
        )

        previous_frame = gray
        kept_frames += 1

        print(f"{filename} | FIRST FRAME | KEEP")

        continue

    # Calculate similarity using normalized correlation
    similarity = cv2.matchTemplate(
        previous_frame,
        gray,
        cv2.TM_CCOEFF_NORMED
    )[0][0]

    # Decide whether frame is different enough
    if similarity < similarity_threshold:

        output_path = os.path.join(
            output_folder,
            filename
        )

        original_image = cv2.imread(image_path)

        cv2.imwrite(
            output_path,
            original_image
        )

        previous_frame = gray

        kept_frames += 1

        print(
            f"{filename} | "
            f"Similarity: {similarity:.4f} | KEEP"
        )

    else:

        redundant_frames += 1

        print(
            f"{filename} | "
            f"Similarity: {similarity:.4f} | REDUNDANT"
        )


print("\n----- RESULTS -----")

print(f"Total frames analyzed: {total_frames}")
print(f"Frames kept: {kept_frames}")
print(f"Redundant frames removed: {redundant_frames}")

