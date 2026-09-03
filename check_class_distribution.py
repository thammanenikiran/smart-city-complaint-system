import os
from collections import Counter

LABEL_DIR = r"C:\Users\kk139\smart-city-complaint-system\dataset\labels"

class_names = {
    0: "pothole",
    1: "damaged_road",
    2: "garbage",
    3: "overflowing_bin",
    4: "broken_streetlight",
    5: "water_leakage",
    6: "damaged_traffic_sign",
    7: "fallen_tree",
    8: "damaged_crosswalk"
}

counts = Counter()

for split in ["train", "val", "test"]:

    folder = os.path.join(
        LABEL_DIR,
        split
    )

    for file in os.listdir(folder):

        if not file.endswith(".txt"):
            continue

        path = os.path.join(folder, file)

        with open(path, "r") as f:

            for line in f:

                parts = line.strip().split()

                if len(parts) >= 5:

                    class_id = int(parts[0])

                    counts[class_id] += 1


print("\n========== CLASS DISTRIBUTION ==========\n")

for class_id, name in class_names.items():

    print(
        f"{class_id} → {name}: "
        f"{counts[class_id]} objects"
    )

print("\n========================================")