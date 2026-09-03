import os
import shutil


# =====================================================
# SOURCE WATER LEAKAGE DATASET
# =====================================================

SOURCE = r"C:\Users\kk139\Downloads\water_leakage_detection.v1i.yolov11"


# =====================================================
# YOUR SMART CITY DATASET
# =====================================================

DEST = r"C:\Users\kk139\smart-city-complaint-system\dataset"


# Source class:
# 0 = water-leakage

SOURCE_CLASS_ID = 0


# Our project class:
# 5 = water_leakage

FINAL_CLASS_ID = 5


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


    # Create destination folders

    os.makedirs(
        destination_images,
        exist_ok=True
    )

    os.makedirs(
        destination_labels,
        exist_ok=True
    )


    copied = 0


    for image_file in os.listdir(source_images):

        if not image_file.lower().endswith(
            (".jpg", ".jpeg", ".png", ".bmp", ".webp")
        ):
            continue


        base_name = os.path.splitext(
            image_file
        )[0]


        source_image = os.path.join(
            source_images,
            image_file
        )


        source_label = os.path.join(
            source_labels,
            base_name + ".txt"
        )


        # Check label

        if not os.path.exists(source_label):

            print(
                "Label missing:",
                image_file
            )

            continue


        # Read labels

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


            # YOLO format:
            # class x_center y_center width height

            if len(parts) != 5:
                continue


            original_class = int(parts[0])


            # -----------------------------------------
            # Keep only water leakage
            # -----------------------------------------

            if original_class == SOURCE_CLASS_ID:

                # Convert:
                # 0 → 5

                parts[0] = str(
                    FINAL_CLASS_ID
                )

                new_lines.append(
                    " ".join(parts)
                )


        # No water leakage annotation

        if not new_lines:
            continue


        # Unique filename

        new_name = (
            f"water_leakage_{copied:06d}"
        )


        extension = os.path.splitext(
            image_file
        )[1]


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


        # Copy image

        shutil.copy2(
            source_image,
            destination_image
        )


        # Write converted label

        with open(
            destination_label,
            "w"
        ) as file:

            file.write(
                "\n".join(new_lines)
            )


        copied += 1


    print(
        f"{source_split}: "
        f"{copied} water-leakage images merged."
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
print("Water leakage dataset merged!")
print("==========================================")