import os
import shutil


SOURCE = r"C:\Users\kk139\Downloads\Pothole Detection.v13i.yolov11"

DEST = r"C:\Users\kk139\smart-city-complaint-system\dataset"

def copy_folder(source_folder, destination_folder):

    os.makedirs(destination_folder, exist_ok=True)

    files = os.listdir(source_folder)

    print(f"Copying {len(files)} files...")
    print(f"FROM: {source_folder}")
    print(f"TO:   {destination_folder}")

    for filename in files:

        source_file = os.path.join(
            source_folder,
            filename
        )

        destination_file = os.path.join(
            destination_folder,
            filename
        )

        if os.path.isfile(source_file):

            shutil.copy2(
                source_file,
                destination_file
            )

    print("Done!")

# =========================
# TRAIN
# =========================

copy_folder(
    os.path.join(SOURCE, "train", "images"),
    os.path.join(DEST, "images", "train")
)

copy_folder(
    os.path.join(SOURCE, "train", "labels"),
    os.path.join(DEST, "labels", "train")
)


# =========================
# VALIDATION
# =========================

copy_folder(
    os.path.join(SOURCE, "valid", "images"),
    os.path.join(DEST, "images", "val")
)

copy_folder(
    os.path.join(SOURCE, "valid", "labels"),
    os.path.join(DEST, "labels", "val")
)


# =========================
# TEST
# =========================

copy_folder(
    os.path.join(SOURCE, "test", "images"),
    os.path.join(DEST, "images", "test")
)

copy_folder(
    os.path.join(SOURCE, "test", "labels"),
    os.path.join(DEST, "labels", "test")
)


print()
print("Pothole dataset copied successfully!")