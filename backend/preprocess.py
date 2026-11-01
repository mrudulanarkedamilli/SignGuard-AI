
import cv2
import numpy as np
from pathlib import Path

BASE = Path("dataset/raw/signatures")
OUTPUT = Path("dataset/processed")
SIZE = (220, 155)

def preprocess_image(path):
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)

    if img is None:
        raise ValueError(f"Cannot read {path}")

    # Convert dark handwriting to white foreground
    _, binary = cv2.threshold(
        img, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # Crop around signature strokes
    points = cv2.findNonZero(binary)

    if points is not None:
        x, y, w, h = cv2.boundingRect(points)
        binary = binary[y:y+h, x:x+w]

    # Preserve aspect ratio and add padding
    target_w, target_h = SIZE
    h, w = binary.shape

    scale = min((target_w - 20) / w, (target_h - 20) / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))

    resized = cv2.resize(
        binary, (new_w, new_h),
        interpolation=cv2.INTER_AREA
    )

    canvas = np.zeros((target_h, target_w), dtype=np.uint8)

    x = (target_w - new_w) // 2
    y = (target_h - new_h) // 2

    canvas[y:y+new_h, x:x+new_w] = resized

    return canvas

def process_dataset():
    for category in ["full_org", "full_forg"]:
        source = BASE / category
        destination = OUTPUT / category
        destination.mkdir(parents=True, exist_ok=True)

        count = 0

        for path in sorted(source.glob("*.png")):
            processed = preprocess_image(path)
            cv2.imwrite(str(destination / path.name), processed)
            count += 1

        print(f"{category}: {count} images processed")

    print("Preprocessing completed successfully!")

if __name__ == "__main__":
    process_dataset()
