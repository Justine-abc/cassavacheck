"""CassaCheck API: five-class cassava leaf diagnosis with district information shown separately.

Run: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
Swagger UI: http://localhost:8000/docs   Web page: http://localhost:8000/
"""
from pathlib import Path
import csv
import io

import torch
import torchvision
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from torchvision import transforms

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEIGHTS_PATH = PROJECT_ROOT / "models" / "mobilenetv3_baseline.pt"
DISTRICT_TABLE = PROJECT_ROOT / "data" / "district_prevalence.csv"
CLASS_NAMES = ["CBB", "CBSD", "CGM", "CMD", "healthy"]   # same order as the Kaggle label ids 0 to 4

app = FastAPI(title="CassaCheck API", version="0.1.0",
              description="Five-class cassava leaf diagnosis. District information is returned by a separate endpoint and is never combined with the image result.")

# ---- model: loaded once at start-up; the server runs without weights so the page still works during development ----
preprocess = transforms.Compose([transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(),
                                 transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
model = torchvision.models.mobilenet_v3_large(weights=None)
model.classifier[-1] = torch.nn.Linear(model.classifier[-1].in_features, len(CLASS_NAMES))
weights_loaded = WEIGHTS_PATH.exists()
if weights_loaded:
    model.load_state_dict(torch.load(WEIGHTS_PATH, map_location="cpu"))
model.eval()


def read_district_table():
    with open(DISTRICT_TABLE, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@app.get("/health")
def health():
    return {"status": "ok", "weights_loaded": weights_loaded, "classes": CLASS_NAMES}


@app.get("/districts")
def districts():
    """Published district incidence with survey year and number of fields: information for the panel, not a probability for a leaf."""
    return read_district_table()


@app.post("/diagnose")
async def diagnose(image: UploadFile = File(...)):
    """Return the five class probabilities for one leaf photo. Calibration and abstention are added in the next version."""
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=415, detail="Upload a JPEG or PNG photograph")
    if not weights_loaded:
        raise HTTPException(status_code=503, detail="Model weights not found in models/; train notebook 02 first")
    picture = Image.open(io.BytesIO(await image.read())).convert("RGB")
    with torch.no_grad():
        probabilities = torch.softmax(model(preprocess(picture).unsqueeze(0)), dim=1)[0].tolist()
    top_index = max(range(len(CLASS_NAMES)), key=lambda index: probabilities[index])
    return {"prediction": CLASS_NAMES[top_index], "confidence": round(probabilities[top_index], 4),
            "probabilities": {name: round(value, 4) for name, value in zip(CLASS_NAMES, probabilities)},
            "note": "Uncalibrated baseline; abstention not yet applied."}


# ---- web page: one static file, served last so the API routes above keep priority ----
app.mount("/static", StaticFiles(directory=PROJECT_ROOT / "api" / "static"), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(PROJECT_ROOT / "api" / "static" / "index.html")
