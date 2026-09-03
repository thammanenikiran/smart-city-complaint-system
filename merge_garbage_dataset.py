import os
import shutil


# =====================================================
# 1. ORIGINAL GARBAGE DATASET
# =====================================================

SOURCE = r"C:\Users\kk139\Downloads\archive (3)\GARBAGE CLASSIFICATION"


# =====================================================
# 2. SMART CITY PROJECT DATASET
# =====================================================

DEST = r"C:\Users\kk139\smart-city-complaint-system\dataset"


# =====================================================
# 3. GARBAGE CLASS ID IN OUR FINAL MODEL
# =====================================================

GARBAGE_CLASS_ID = 2


# =====================================================
# FUNCTION TO MERGE ONE SPLIT
# =====================================================

def merge_split(split_name, destination_split):

    source_images = os.path.join(
        SOURCE,
        split_name,
        "images"
    )

    source_labels = os.path.join(
        SOURCE,
        split_name,
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


    # Create destination folders if necessary
    os.makedirs(destination_images, exist_ok=True)
    os.makedirs(destination_labels, exist_ok=True)


    if not os.path.exists(source_images):
        print("Images folder not found:")
        print(source_images)
        return


    if not os.path.exists(source_labels):
        print("Labels folder not found:")
        print(source_labels)
        return


    image_files = os.listdir(source_images)

    count = 0


    for image_file in image_files:

        source_image = os.path.join(
            source_images,
            image_file
        )


        # Ignore non-image files
        if not image_file.lower().endswith(
            (".jpg", ".jpeg", ".png", ".bmp", ".webp")
        ):
            continue


        # Get original filename without extension
        base_name = os.path.splitext(image_file)[0]


        # New filename
        new_name = f"garbage_{count:06d}"


        # Preserve image extension
        extension = os.path.splitext(image_file)[1]


        new_image_name = new_name + extension


        # Original label
        source_label = os.path.join(
            source_labels,
            base_name + ".txt"
        )


        # Destination files
        destination_image = os.path.join(
            destination_images,
            new_image_name
        )

        destination_label = os.path.join(
            destination_labels,
            new_name + ".txt"
        )


        # ---------------------------------------------
        # COPY IMAGE
        # ---------------------------------------------

        shutil.copy2(
            source_image,
            destination_image
        )


        # ---------------------------------------------
        # CONVERT LABEL
        # ---------------------------------------------

        if os.path.exists(source_label):

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


                # YOLO format must have 5 values
                if len(parts) != 5:
                    print(
                        "WARNING: Invalid label:",
                        source_label
                    )
                    continue


                # Change original class ID
                # 0-5 → 2

                parts[0] = str(
                    GARBAGE_CLASS_ID
                )


                new_lines.append(
                    " ".join(parts)
                )


            # Write converted label

            with open(
                destination_label,
                "w"
            ) as file:

                file.write(
                    "\n".join(new_lines)
                )


        else:

            print(
                "WARNING: Label not found:",
                source_label
            )


        count += 1


    print(
        f"{split_name}: {count} garbage images merged."
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
print("====================================")
print("Garbage dataset merged successfully!")
print("====================================")