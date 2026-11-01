
from pathlib import Path
import cv2

base = Path("dataset/raw/signatures")

for folder in ["full_org", "full_forg"]:
    path = base / folder
    files = sorted(
        p for p in path.iterdir()
        if p.is_file() and p.suffix.lower() in
        [".png", ".jpg", ".jpeg", ".bmp"]
    )

    valid = 0
    invalid = []

    for file in files:
        image = cv2.imread(str(file), cv2.IMREAD_GRAYSCALE)
        if image is not None:
            valid += 1
        else:
            invalid.append(file.name)

    print(f"\nFolder: {folder}")
    print(f"Image files: {len(files)}")
    print(f"Readable images: {valid}")
    print(f"Unreadable images: {invalid}")
