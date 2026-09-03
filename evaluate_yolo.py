from ultralytics import YOLO


def main():

    model = YOLO(
        r"C:\Users\kk139\runs\detect\runs\smart_city_final-2\weights\best.pt"
    )

    metrics = model.val(
        data="dataset/data.yaml",
        imgsz=640,
        batch=8,
        device=0,
        workers=2
    )

    print("\n====================================")
    print("OVERALL RESULTS")
    print("====================================")

    print("Precision:", metrics.box.mp)
    print("Recall:", metrics.box.mr)
    print("mAP50:", metrics.box.map50)
    print("mAP50-95:", metrics.box.map)

    print("\n====================================")
    print("CLASS-WISE RESULTS")
    print("====================================")

    for i, class_name in model.names.items():

        print(
            f"{i} - {class_name}: "
            f"AP50 = {metrics.box.ap50[i]:.3f}, "
            f"AP50-95 = {metrics.box.ap[i]:.3f}"
        )


if __name__ == "__main__":
    main()