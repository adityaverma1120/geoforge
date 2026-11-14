import cv2
import os

input_folder = "../frames"

scores = []

for filename in os.listdir(input_folder):

    if filename.endswith(".jpg"):

        image_path = os.path.join(input_folder, filename)

        image = cv2.imread(image_path)

        if image is None:
            continue

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        sharpness_score = cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()

        scores.append(sharpness_score)


print("\n----- SHARPNESS ANALYSIS -----")

print(f"Total frames analyzed: {len(scores)}")
print(f"Minimum score: {min(scores):.2f}")
print(f"Maximum score: {max(scores):.2f}")
print(f"Average score: {sum(scores) / len(scores):.2f}")

print("\n----- SCORE DISTRIBUTION -----")

ranges = [
    (0, 300),
    (300, 400),
    (400, 500),
    (500, 600),
    (600, 700),
    (700, 900),
    (900, float("inf"))
]

for minimum, maximum in ranges:

    if maximum == float("inf"):

        count = sum(score >= minimum for score in scores)

        print(f"{minimum}+ : {count} frames")

    else:

        count = sum(
            minimum <= score < maximum
            for score in scores
        )

        print(
            f"{minimum}-{maximum}: "
            f"{count} frames"
        )
        