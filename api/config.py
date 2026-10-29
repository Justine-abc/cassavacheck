"""Paths and constants shared by the API. Nothing here is tuned; tuned values live in models/calibration.json."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIRECTORY = PROJECT_ROOT / "models"
WEIGHTS_PATH = MODELS_DIRECTORY / "mobilenetv3_baseline.pt"
CALIBRATION_PATH = MODELS_DIRECTORY / "calibration.json"
DISTRICT_TABLE_PATH = PROJECT_ROOT / "data" / "district_prevalence.csv"
# Overridable so the test suite writes to a temporary log instead of the officer's real one.
LOG_DATABASE_PATH = Path(os.environ.get("CASSACHECK_LOG_PATH", PROJECT_ROOT / "data" / "diagnosis_log.sqlite"))
STATIC_DIRECTORY = PROJECT_ROOT / "api" / "static"

# Same order as the Kaggle label ids 0 to 4; the model's output index is this list's index.
CLASS_NAMES = ["CBB", "CBSD", "CGM", "CMD", "healthy"]
CLASS_LONG_NAMES = {
    "CBB": "Cassava bacterial blight",
    "CBSD": "Cassava brown streak disease",
    "CGM": "Cassava green mite",
    "CMD": "Cassava mosaic disease",
    "healthy": "Healthy",
}
ACCEPTED_IMAGE_TYPES = {"image/jpeg", "image/png"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
