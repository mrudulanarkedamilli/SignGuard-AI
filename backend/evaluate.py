
import sys
from pathlib import Path
import random
import re
import json

import cv2
import numpy as np
import torch
import matplotlib.pyplot as plt

from sklearn.metrics import (
    accuracy_score, precision_score,
    recall_score, f1_score,
    confusion_matrix, roc_auc_score,
    roc_curve
)

sys.path.insert(0, str(Path(__file__).parent))
from model import SiameseNetwork

SEED = 42
random.seed(SEED)

BASE = Path("dataset/processed")
DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

def writer_id(path):
    match = re.search(r"_(\d+)_(\d+)$", path.stem)
    if not match:
        raise ValueError(f"Invalid filename: {path.name}")
    return int(match.group(1))

def load_groups(folder):
    groups = {}
    for path in sorted((BASE / folder).glob("*.png")):
        groups.setdefault(writer_id(path), []).append(path)
    return groups

genuine = load_groups("full_org")
forged = load_groups("full_forg")

# Reproduce the writer split from train.py
writers = sorted(set(genuine) & set(forged))
random.shuffle(writers)

n = len(writers)
val_ids = writers[int(n * 0.7):int(n * 0.85)]
test_ids = writers[int(n * 0.85):]

def create_pairs(ids):
    rng = random.Random(SEED + 10)
    pairs = []

    for wid in ids:
        originals = genuine[wid]
        fakes = forged[wid]

        for _ in range(15):
            a, b = rng.sample(originals, 2)
            pairs.append((a, b, 1))

            a = rng.choice(originals)
            b = rng.choice(fakes)
            pairs.append((a, b, 0))

    # Different-writer genuine pairs
    for wid in ids:
        others = [w for w in ids if w != wid]
        for _ in range(15):
            other = rng.choice(others)
            pairs.append((
                rng.choice(genuine[wid]),
                rng.choice(genuine[other]),
                0
            ))

    rng.shuffle(pairs)
    return pairs

def read_image(path):
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Cannot read: {path}")
    img = img.astype(np.float32) / 255.0
    return torch.from_numpy(img).unsqueeze(0).unsqueeze(0)

model = SiameseNetwork().to(DEVICE)
model.load_state_dict(
    torch.load(
        "models/siamese_model.pth",
        map_location=DEVICE,
        weights_only=True
    )
)
model.eval()

def predict_pairs(pairs):
    labels, scores = [], []

    with torch.no_grad():
        for a, b, label in pairs:
            x1 = read_image(a).to(DEVICE)
            x2 = read_image(b).to(DEVICE)

            z1, z2 = model(x1, x2)
            distance = torch.nn.functional.pairwise_distance(
                z1, z2
            ).item()

            # Larger score means more similar
            score = -distance

            labels.append(label)
            scores.append(score)

    return np.array(labels), np.array(scores)

print("Evaluating validation signatures...", flush=True)
val_labels, val_scores = predict_pairs(create_pairs(val_ids))

# Select threshold using validation data only
fpr, tpr, thresholds = roc_curve(val_labels, val_scores)
best_index = np.argmax(tpr - fpr)
threshold = float(thresholds[best_index])

print("Evaluating unseen test writers...", flush=True)
test_labels, test_scores = predict_pairs(create_pairs(test_ids))
predictions = (test_scores >= threshold).astype(int)

cm = confusion_matrix(test_labels, predictions, labels=[0, 1])
tn, fp, fn, tp = cm.ravel()

results = {
    "threshold": threshold,
    "accuracy": float(accuracy_score(test_labels, predictions)),
    "precision": float(precision_score(
        test_labels, predictions, zero_division=0
    )),
    "recall": float(recall_score(
        test_labels, predictions, zero_division=0
    )),
    "f1_score": float(f1_score(
        test_labels, predictions, zero_division=0
    )),
    "roc_auc": float(roc_auc_score(test_labels, test_scores)),
    "false_acceptance_rate": float(fp / (fp + tn)),
    "false_rejection_rate": float(fn / (fn + tp)),
    "confusion_matrix": cm.tolist(),
    "test_pairs": len(test_labels),
    "test_writers": len(test_ids)
}

Path("reports").mkdir(exist_ok=True)
Path("models").mkdir(exist_ok=True)

with open("models/threshold.json", "w") as f:
    json.dump({"threshold": threshold}, f, indent=4)

with open("reports/evaluation.json", "w") as f:
    json.dump(results, f, indent=4)

print("\n===== MODEL EVALUATION =====")
for key, value in results.items():
    print(f"{key}: {value}")

plt.figure(figsize=(6, 5))
plt.imshow(cm, cmap="Blues")
plt.colorbar()
plt.xticks([0, 1], ["Different/Forged", "Same Writer"])
plt.yticks([0, 1], ["Different/Forged", "Same Writer"])
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Signature Verification Confusion Matrix")

for i in range(2):
    for j in range(2):
        plt.text(
            j, i, str(cm[i, j]),
            ha="center", va="center",
            color="red"
        )

plt.tight_layout()
plt.savefig("reports/confusion_matrix.png", dpi=150)
plt.close()

print("\nEvaluation completed successfully!")
print("Saved: reports/evaluation.json")
print("Saved: reports/confusion_matrix.png")
print("Saved: models/threshold.json")
