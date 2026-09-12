import subprocess
from pathlib import Path


# ==========================================
# COLMAP LOCATION
# ==========================================

COLMAP = r"C:\bin\colmap.exe"


# ==========================================
# JOB ID
# ==========================================

JOB_ID = "8f9f2cd7-a882-45d5-92df-fea1f54bbcca"


# ==========================================
# DIRECTORIES
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

IMAGE_DIR = (
    BASE_DIR
    / "temp"
    / JOB_ID
    / "final_frames"
)

WORKSPACE_DIR = (
    BASE_DIR
    / "temp"
    / JOB_ID
    / "colmap"
)


# ==========================================
# RUN COLMAP COMMAND
# ==========================================

def run_colmap(command, args):

    print()
    print("================================")
    print(f"Running COLMAP: {command}")
    print("================================")

    cmd = [COLMAP, command] + args

    print(" ".join(str(x) for x in cmd))

    result = subprocess.run(cmd)

    if result.returncode != 0:

        raise RuntimeError(
            f"COLMAP command failed with exit code "
            f"{result.returncode}"
        )

    print()
    print(f"{command} completed successfully.")


# ==========================================
# MAIN PIPELINE
# ==========================================

def main():

    # Check image folder

    if not IMAGE_DIR.exists():

        raise RuntimeError(
            f"Image directory does not exist:\n"
            f"{IMAGE_DIR}"
        )


    # Create COLMAP workspace

    WORKSPACE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    # Database location

    database_path = (
        WORKSPACE_DIR
        / "database.db"
    )


    print()
    print("================================")
    print("COLMAP PIPELINE")
    print("================================")

    print(f"Images: {IMAGE_DIR}")
    print(f"Workspace: {WORKSPACE_DIR}")
    print(f"Database: {database_path}")


    # ======================================
    # STEP 1
    # FEATURE EXTRACTION
    # ======================================

    run_colmap(
        "feature_extractor",
        [
            "--database_path",
            str(database_path),

            "--image_path",
            str(IMAGE_DIR)
        ]
    )


    # ======================================
    # STEP 2
    # FEATURE MATCHING
    # ======================================

    run_colmap(
        "exhaustive_matcher",
        [
            "--database_path",
            str(database_path)
        ]
    )


    # ======================================
    # STEP 3
    # SPARSE RECONSTRUCTION
    # ======================================

    sparse_dir = (
        WORKSPACE_DIR
        / "sparse"
    )

    sparse_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    run_colmap(
        "mapper",
        [
            "--database_path",
            str(database_path),

            "--image_path",
            str(IMAGE_DIR),

            "--output_path",
            str(sparse_dir)
        ]
    )


    # ======================================
    # COMPLETE
    # ======================================

    print()
    print("================================")
    print("COLMAP SPARSE RECONSTRUCTION DONE")
    print("================================")

    print()
    print("Sparse reconstruction location:")

    print(sparse_dir)


# ==========================================
# START PROGRAM
# ==========================================

if __name__ == "__main__":
    main()
