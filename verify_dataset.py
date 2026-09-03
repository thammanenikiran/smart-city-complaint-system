import os

DATASET = r"C:\Users\kk139\smart-city-complaint-system\dataset"

splits = ["train", "val", "test"]

valid_classes = {0, 1, 2, 3, 4, 5, 6, 7, 8}

for split in splits:

    image_folder = os.path.join(
        DATASET,
        "images",
        split
    )

    label_folder = os.path.join(
        DATASET,
        "labels",
        split
    )

    images = [
        f for f in os.listdir(image_folder)
        if f.lower().endswith(
            (".jpg", ".jpeg", ".png", ".bmp", ".webp")
        )
    ]

    labels = [
        f for f in os.listdir(label_folder)
        if f.endswith(".txt")
    ]

    image_names = {
        os.path.splitext(f)[0]
        for f in images
    }

    label_names = {
        os.path.splitext(f)[0]
        for f in labels
    }

    missing_labels = image_names - label_names
    missing_images = label_names - image_names

    invalid_labels = []

    for label_file in labels:

        path = os.path.join(
            label_folder,
            label_file
        )

        with open(path, "r") as file:
            lines = file.readlines()

        for line_number, line in enumerate(lines, 1):

            line = line.strip()

            if not line:
                continue

            parts = line.split()

            if len(parts) != 5:

                invalid_labels.append(
                    f"{label_file}: line {line_number}"
                )

                continue

            class_id = int(parts[0])

            if class_id not in valid_classes:

                invalid_labels.append(
                    f"{label_file}: class {class_id}"
                )

    print()
    print("==============================")
    print(f"{split.upper()} DATASET")
    print("==============================")

    print("Images :", len(images))
    print("Labels :", len(labels))

    print(
        "Missing labels:",
        len(missing_labels)
    )

    print(
        "Missing images:",
        len(missing_images)
    )

    print(
        "Invalid labels:",
        len(invalid_labels)
    )


print()
print("==============================")
print("DATASET VERIFICATION COMPLETE")
print("==============================")