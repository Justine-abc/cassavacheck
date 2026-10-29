"""CassaCheck API: routes only. Every piece of logic lives in its own module (classifier, calibration, districts, advice, log_store).

Run: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
Swagger UI: http://localhost:8000/docs   Web page: http://localhost:8000/
"""
import io

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

from api import config
from api.advice import AdvisoryService
from api.calibration import AbstentionGate, CalibrationSettings, Calibrator
from api.classifier import MobileNetV3Classifier
from api.districts import DistrictRepository
from api.log_store import DiagnosisLog

app = FastAPI(title="CassaCheck API", version="0.2.0",
              description="Five-class cassava leaf diagnosis with calibrated confidence and abstention. "
                          "District information is served separately and never changes the diagnosis.")

# Built once at start-up; each object has one responsibility and can be swapped (another backbone, PostgreSQL log) without touching routes.
classifier = MobileNetV3Classifier(config.WEIGHTS_PATH)
settings = CalibrationSettings.load(config.CALIBRATION_PATH)
calibrator = Calibrator(settings.temperature)
gate = AbstentionGate(settings.threshold)
advisory = AdvisoryService()
districts = DistrictRepository(config.DISTRICT_TABLE_PATH)
log = DiagnosisLog(config.LOG_DATABASE_PATH)
MODEL_VERSION = f"{classifier.name}:{config.WEIGHTS_PATH.name}:T{settings.temperature}:tau{settings.threshold}"


@app.get("/health")
def health():
    return {"status": "ok", "weights_loaded": classifier.weights_loaded, "classes": config.CLASS_NAMES,
            "temperature": settings.temperature, "threshold": settings.threshold, "calibration_fitted_on": settings.fitted_on}


@app.get("/districts")
def list_districts():
    """Published district incidence with survey year and number of fields: information for the panel, not a probability for a leaf."""
    return districts.all_rows()


@app.get("/districts/choices")
def district_choices():
    """All 30 districts for the picker, each flagged with whether a published survey value exists."""
    return districts.choices()


@app.get("/log")
def recent_log(limit: int = 50, district: str | None = None):
    """Extension-officer view: anonymised recent requests (date, district, season, decision, confidence)."""
    return log.recent(limit=min(limit, 200), district=district)


@app.post("/diagnose")
async def diagnose(image: UploadFile = File(...), district: str | None = Form(default=None), season: str | None = Form(default=None)):
    """One leaf photo in; calibrated probabilities, a label or an abstention, advice, and the district panel out."""
    if image.content_type not in config.ACCEPTED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPEG or PNG photograph")
    if not classifier.weights_loaded:
        raise HTTPException(status_code=503, detail="Model weights not found in models/; run notebook 02 first")
    raw_bytes = await image.read()
    if len(raw_bytes) > config.MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image larger than 10 MB")
    try:
        picture = Image.open(io.BytesIO(raw_bytes))
        picture.load()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=422, detail="The file is not a readable image")

    logits = classifier.predict_logits(picture)
    decision = gate.decide(calibrator.calibrate(logits))
    guidance = advisory.advice_for(decision)
    panel = districts.lookup(district, season or "A") if district else None
    diagnosis_id = log.record(district, season, decision, MODEL_VERSION)

    return {
        "diagnosis_id": diagnosis_id,
        "decision": "abstain" if decision.abstained else decision.label,
        "label_long": None if decision.abstained else config.CLASS_LONG_NAMES[decision.label],
        "confidence": decision.confidence,
        "threshold": settings.threshold,
        "probabilities": decision.probabilities,
        "advice": guidance["advice"],
        "follow_up_questions": guidance["follow_up_questions"],
        "referral": guidance["referral"],
        "district_panel": panel.sentence() if panel else None,
        "model_version": MODEL_VERSION,
    }


class FollowUp(BaseModel):
    diagnosis_id: int
    answers: dict[str, str] = {}
    referral_requested: bool = False


@app.post("/follow_up")
def follow_up(body: FollowUp):
    """The farmer's answers to the follow-up questions and, if asked, a referral to the extension officer.
    Adds guidance and goes to the officer's log; the diagnosis and its probabilities are never recomputed."""
    if not log.exists(body.diagnosis_id):
        raise HTTPException(status_code=404, detail="Unknown diagnosis")
    answers = advisory.valid_answers(body.answers)
    log.add_follow_up(body.diagnosis_id, answers, body.referral_requested)
    return {"diagnosis_id": body.diagnosis_id, "answers": answers, "guidance": advisory.guidance_for_answers(answers),
            "referral_requested": body.referral_requested}


app.mount("/static", StaticFiles(directory=config.STATIC_DIRECTORY), name="static")


# One HTML file per screen of the design; all logic is in the API, the pages only call it.
PAGES = {"/": "index.html", "/result": "result.html", "/how-it-works": "how_it_works.html", "/officer": "officer.html"}


def page_route(file_name: str):
    return lambda: FileResponse(config.STATIC_DIRECTORY / file_name)


for path, file_name in PAGES.items():
    app.get(path, include_in_schema=False)(page_route(file_name))
