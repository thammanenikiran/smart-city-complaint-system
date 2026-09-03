import os
import shutil


# =====================================================
# SOURCE: WASTE BIN DATASET
# =====================================================

SOURCE = r"C:\Users\kk139\Downloads\Waste_Bin_Fill_Level"


# =====================================================
# DESTINATION: SMART CITY DATASET
# =====================================================

DEST = r"C:\Users\kk139\smart-city-complaint-system\dataset"


# =====================================================
# SOURCE CLASS
# =====================================================

OVERFLOWING_CLASS_ID = 3


# =====================================================
# OUR FINAL CLASS
# =====================================================

FINAL_CLASS_ID = 3


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


    image_files = os.listdir(source_images)

    copied = 0


    for image_file in image_files:

        # Only images

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


        # Label must exist

        if not os.path.exists(source_label):

            print(
                "Label missing:",
                image_file
            )

            continue


        # Read original annotations

        with open(
            source_label,
            "r"
        ) as file:

            lines = file.readlines()


        overflowing_lines = []


        for line in lines:

            line = line.strip()


            if not line:
                continue


            parts = line.split()


            # YOLO format:
            # class x y width height

            if len(parts) != 5:

                continue


            original_class = int(parts[0])


            # -----------------------------------------
            # KEEP ONLY OVERFLOWING
            # -----------------------------------------

            if original_class == OVERFLOWING_CLASS_ID:

                parts[0] = str(
                    FINAL_CLASS_ID
                )

                overflowing_lines.append(
                    " ".join(parts)
                )


        # -----------------------------------------
        # Ignore images that don't contain
        # overflowing bins
        # -----------------------------------------

        if not overflowing_lines:

            continue


        # -----------------------------------------
        # Create unique filename
        # -----------------------------------------

        new_name = (
            f"overflowing_bin_{copied:06d}"
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


        # -----------------------------------------
        # Copy image
        # -----------------------------------------

        shutil.copy2(
            source_image,
            destination_image
        )


        # -----------------------------------------
        # Write only overflowing annotations
        # -----------------------------------------

        with open(
            destination_label,
            "w"
        ) as file:

            file.write(
                "\n".join(
                    overflowing_lines
                )
            )


        copied += 1


    print(
        f"{source_split}: "
        f"{copied} overflowing-bin images merged."
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
print("Overflowing-bin dataset merged!")
print("==========================================")