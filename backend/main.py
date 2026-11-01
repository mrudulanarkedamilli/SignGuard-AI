
from backend.auth import router as auth_router
from backend.auth import get_current_user
from fastapi import Depends
from pathlib import Path
from io import BytesIO
import json

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, UnidentifiedImageError

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.model import SiameseNetwork

ROOT = Path(__file__).resolve().parent.parent
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

app = FastAPI(
    title="SignGuard AI API",
    description="Deep Learning Signature Verification",
    version="1.0.0"
)
app.include_router(auth_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

model = SiameseNetwork().to(DEVICE)

model_path = ROOT / "models" / "siamese_model.pth"
threshold_path = ROOT / "models" / "threshold.json"

if not model_path.exists() or not threshold_path.exists():
    raise RuntimeError(
        "Model or threshold missing. Complete Steps 6 and 7."
    )

model.load_state_dict(
    torch.load(model_path, map_location=DEVICE, weights_only=True)
)
model.eval()

with open(threshold_path, "r") as f:
    THRESHOLD = float(json.load(f)["threshold"])


def preprocess(image):
    import cv2

    gray = np.array(image.convert("L"))

    _, binary = cv2.threshold(
        gray, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    points = cv2.findNonZero(binary)

    if points is not None:
        x, y, w, h = cv2.boundingRect(points)
        binary = binary[y:y+h, x:x+w]

    target_w, target_h = 220, 155
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

    tensor = torch.from_numpy(
        canvas.astype(np.float32) / 255.0
    ).unsqueeze(0).unsqueeze(0)

    return tensor.to(DEVICE)


async def read_signature(upload):
    if upload.content_type not in (
        "image/png", "image/jpeg", "image/bmp"
    ):
        raise HTTPException(400, "Upload a PNG, JPEG, or BMP image.")

    data = await upload.read(5 * 1024 * 1024 + 1)

    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "Image must be under 5 MB.")

    try:
        image = Image.open(BytesIO(data))
        image.load()
        return image
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(400, "Invalid image file.")


@app.get("/")
def home():
    return {
        "application": "SignGuard AI",
        "status": "running",
        "model": "Siamese CNN"
    }


@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": True}


@app.post("/predict", dependencies=[Depends(get_current_user)])
async def predict(
    reference: UploadFile = File(...),
    test: UploadFile = File(...)
):
    image1 = await read_signature(reference)
    image2 = await read_signature(test)

    x1 = preprocess(image1)
    x2 = preprocess(image2)

    with torch.no_grad():
        z1, z2 = model(x1, x2)
        distance = F.pairwise_distance(z1, z2).item()

    score = -distance
    same_writer = bool(score >= THRESHOLD)

    return {
        "prediction": (
            "Likely Same Writer"
            if same_writer else "Likely Different Writer"
        ),
        "same_writer": same_writer,
        "distance": round(distance, 4),
        "similarity_score": round(score, 4),
        "threshold": round(THRESHOLD, 4),
        "message": (
            "Experimental AI prediction, not proof of authenticity."
        )
    }

@app.get("/metrics", dependencies=[Depends(get_current_user)])
def get_metrics():
    report_path = ROOT / "reports" / "evaluation.json"

    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Evaluation report not found"
        )

    with open(report_path, "r") as file:
        return json.load(file)

