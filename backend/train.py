
import sys
from pathlib import Path
import random
import re
import numpy as np
import cv2
import torch
from torch.utils.data import Dataset, DataLoader

sys.path.insert(0, str(Path(__file__).parent))
from model import SiameseNetwork, ContrastiveLoss

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

BASE = Path("dataset/processed")
DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

def writer_id(path):
    # CEDAR naming: original_1_1.png, forgeries_1_1.png
    match = re.search(r"_(\d+)_(\d+)$", path.stem)
    if not match:
        raise ValueError(f"Unexpected filename: {path.name}")
    return int(match.group(1))

def load_groups(folder):
    groups = {}
    for path in sorted((BASE / folder).glob("*.png")):
        wid = writer_id(path)
        groups.setdefault(wid, []).append(path)
    return groups

genuine = load_groups("full_org")
forged = load_groups("full_forg")

writers = sorted(set(genuine) & set(forged))
random.shuffle(writers)

n = len(writers)
train_ids = writers[:int(n * 0.7)]
val_ids = writers[int(n * 0.7):int(n * 0.85)]
test_ids = writers[int(n * 0.85):]

print("Writers:", n)
print("Train:", len(train_ids),
      "Validation:", len(val_ids),
      "Test:", len(test_ids))

def make_pairs(ids, pairs_per_writer=20):
    pairs = []

    for wid in ids:
        originals = genuine[wid]
        fakes = forged[wid]

        if len(originals) < 2 or not fakes:
            continue

        for _ in range(pairs_per_writer):
            a, b = random.sample(originals, 2)
            pairs.append((a, b, 1.0))

            a = random.choice(originals)
            b = random.choice(fakes)
            pairs.append((a, b, 0.0))

    random.shuffle(pairs)
    return pairs

class SignatureDataset(Dataset):
    def __init__(self, pairs):
        self.pairs = pairs

    def __len__(self):
        return len(self.pairs)

    def read_image(self, path):
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Cannot read {path}")
        img = img.astype(np.float32) / 255.0
        return torch.from_numpy(img).unsqueeze(0)

    def __getitem__(self, index):
        a, b, label = self.pairs[index]
        return (
            self.read_image(a),
            self.read_image(b),
            torch.tensor(label, dtype=torch.float32)
        )

train_pairs = make_pairs(train_ids, 30)
val_pairs = make_pairs(val_ids, 15)
test_pairs = make_pairs(test_ids, 15)

train_loader = DataLoader(
    SignatureDataset(train_pairs),
    batch_size=16,
    shuffle=True,
    num_workers=0
)

val_loader = DataLoader(
    SignatureDataset(val_pairs),
    batch_size=16,
    num_workers=0
)

model = SiameseNetwork().to(DEVICE)
criterion = ContrastiveLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

EPOCHS = 5
best_loss = float("inf")

Path("models").mkdir(exist_ok=True)

for epoch in range(EPOCHS):
    model.train()
    total_loss = 0

    for img1, img2, labels in train_loader:
        img1 = img1.to(DEVICE)
        img2 = img2.to(DEVICE)
        labels = labels.to(DEVICE)

        optimizer.zero_grad()
        out1, out2 = model(img1, img2)
        loss = criterion(out1, out2, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * len(labels)

    train_loss = total_loss / len(train_pairs)

    model.eval()
    val_loss = 0

    with torch.no_grad():
        for img1, img2, labels in val_loader:
            img1 = img1.to(DEVICE)
            img2 = img2.to(DEVICE)
            labels = labels.to(DEVICE)

            out1, out2 = model(img1, img2)
            loss = criterion(out1, out2, labels)
            val_loss += loss.item() * len(labels)

    val_loss /= len(val_pairs)

    print(
        f"Epoch {epoch+1}/{EPOCHS} | "
        f"Train Loss: {train_loss:.4f} | "
        f"Val Loss: {val_loss:.4f}",
        flush=True
    )

    if val_loss < best_loss:
        best_loss = val_loss
        torch.save(
            model.state_dict(),
            "models/siamese_model.pth"
        )

print("\nTraining completed!")
print("Model saved: models/siamese_model.pth")
