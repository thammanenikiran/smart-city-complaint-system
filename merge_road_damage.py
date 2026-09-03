import os
import shutil


# =====================================================
# ORIGINAL ROAD DAMAGE DATASET
# =====================================================

SOURCE = r"C:\Users\kk139\Downloads\Road damage detection.v1i.yolov11"


# =====================================================
# YOUR SMART CITY DATASET
# =====================================================

DEST = r"C:\Users\kk139\smart-city-complaint-system\dataset"


# =====================================================
# OUR CLASS ID
# =====================================================

DAMAGED_ROAD_CLASS_ID = 1


# Original Road Damage class IDs
# 0 = D00
# 1 = D10
# 2 = D20
# 3 = D40
# 4 = D43
# 5 = D44
# 6 = D50

# Classes we want to convert to damaged_road
ROAD_DAMAGE_CLASSES = {
    0,  # D00 - longitudinal crack
    1,  # D10 - transverse crack
    2,  # D20 - alligator crack
    4,  # D43 - damaged crosswalk
    5,  # D44 - damaged paint
    6   # D50 - manhole-related issue
}

# D40 (class 3) is pothole.
# We intentionally SKIP it.


def merge_split(source_split, destination_split):

    source_images = os.path.join(
        SOURCE,
        source_split,
        "images"
    )

    source_labels = os.path.join(
        SOURCE,
        source_split,
        "labels"
    )

    destination_images = os.path.join(
        DEST,
        "images",
        destination_split
    )

    destination_labels = os.path.join(
        DEST,
        "labels",
        destination_split
    )


    # Check source folders

    if not os.path.exists(source_images):

        print("Images folder not found:")
        print(source_images)
        return


    if not os.path.exists(source_labels):

        print("Labels folder not found:")
        print(source_labels)
        return


    os.makedirs(
        destination_images,
        exist_ok=True
    )

    os.makedirs(
        destination_labels,
        exist_ok=True
    )


    image_files = os.listdir(source_images)

    image_count = 0
    label_count = 0


    for image_file in image_files:

        # Only process images

        if not image_file.lower().endswith(
            (".jpg", ".jpeg", ".png", ".bmp", ".webp")
        ):
            continue


        source_image = os.path.join(
            source_images,
            image_file
        )


        base_name = os.path.splitext(
            image_file
        )[0]


        extension = os.path.splitext(
            image_file
        )[1]


        source_label = os.path.join(
            source_labels,
            base_name + ".txt"
        )


        # ---------------------------------------------
        # Read original label
        # ---------------------------------------------

        if not os.path.exists(source_label):

            print(
                "WARNING: Label missing:",
                image_file
            )

            continue


        with open(
            source_label,
            "r"
        ) as file:

            lines = file.readlines()


        new_lines = []


        for line in lines:

            line = line.strip()


            if not line:
                continue


            parts = line.split()


            if len(parts) != 5:

                print(
                    "WARNING: Invalid label:",
                    source_label
                )

                continue


            original_class = int(parts[0])


            # -----------------------------------------
            # Skip D40 = pothole
            # -----------------------------------------

            if original_class == 3:

                continue


            # -----------------------------------------
            # Convert road damage classes
            # to our class ID 1
            # -----------------------------------------

            if original_class in ROAD_DAMAGE_CLASSES:

                parts[0] = str(
                    DAMAGED_ROAD_CLASS_ID
                )

                new_lines.append(
                    " ".join(parts)
                )


        # ---------------------------------------------
        # If image contains ONLY potholes,
        # don't copy it.
        # ---------------------------------------------

        if not new_lines:

            continue


        # ---------------------------------------------
        # Create unique filename
        # ---------------------------------------------

        new_name = (
            f"road_damage_{image_count:06d}"
        )


        new_image_name = (
            new_name + extension
        )


        new_label_name = (
            new_name + ".txt"
        )


        destination_image = os.path.join(
            destination_images,
            new_image_name
        )


        destination_label = os.path.join(
            destination_labels,
            new_label_name
        )


        # ---------------------------------------------
        # Copy image
        # ---------------------------------------------

        shutil.copy2(
            source_image,
            destination_image
        )


        # ---------------------------------------------
        # Save converted label
        # ---------------------------------------------

        with open(
            destination_label,
            "w"
        ) as file:

            file.write(
                "\n".join(new_lines)
            )


        image_count += 1
        label_count += 1


    print()
    print(
        f"{source_split}: "
        f"{image_count} road-damage images merged."
    )


# =====================================================
# TRAIN
# =====================================================

merge_split(
    "train",
    "train"
)


# =====================================================
# VALIDATION
# =====================================================

merge_split(
    "valid",
    "val"
)


# =====================================================
# TEST
# =====================================================

merge_split(
    "test",
    "test"
)


print()
print("==========================================")
print("Road Damage dataset merged successfully!")
print("==========================================")