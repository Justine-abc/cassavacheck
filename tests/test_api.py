"""Integration tests through the HTTP layer. Diagnosis tests are skipped automatically when the weights file is absent."""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api import config
from api.main import app

client = TestClient(app)


def green_leaf_jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (320, 240), (60, 140, 50)).save(buffer, format="JPEG")
    return buffer.getvalue()


def test_health_lists_five_classes():
    body = client.get("/health").json()
    assert body["classes"] == ["CBB", "CBSD", "CGM", "CMD", "healthy"] and "threshold" in body


def test_districts_endpoint_returns_rows():
    rows = client.get("/districts").json()
    assert isinstance(rows, list) and rows and "fields_surveyed" in rows[0]


def test_wrong_file_type_is_rejected_with_415():
    response = client.post("/diagnose", files={"image": ("notes.txt", b"hello", "text/plain")})
    assert response.status_code == 415


def test_corrupt_image_is_rejected_with_422():
    response = client.post("/diagnose", files={"image": ("broken.jpg", b"not really a jpeg", "image/jpeg")})
    assert response.status_code in (422, 503)   # 503 only when weights are absent on the test machine


@pytest.mark.skipif(not config.WEIGHTS_PATH.exists(), reason="model weights not present")
def test_diagnose_returns_schema_and_district_panel():
    response = client.post("/diagnose", data={"district": "Nyanza", "season": "A"},
                           files={"image": ("leaf.jpg", green_leaf_jpeg(), "image/jpeg")})
    assert response.status_code == 200
    body = response.json()
    assert set(body["probabilities"]) == {"CBB", "CBSD", "CGM", "CMD", "healthy"}
    assert abs(sum(body["probabilities"].values()) - 1.0) < 0.01
    assert body["decision"] in {"abstain", "CBB", "CBSD", "CGM", "CMD", "healthy"}
    assert (body["decision"] == "abstain") == (body["confidence"] < body["threshold"])
    assert body["district_panel"] is not None and "Nyanza" in body["district_panel"]
@pytest.mark.skipif(not config.WEIGHTS_PATH.exists(), reason="model weights not present")
def test_district_does_not_change_the_probabilities():
    photo = green_leaf_jpeg()
    with_district = client.post("/diagnose", data={"district": "Nyanza", "season": "A"}, files={"image": ("leaf.jpg", photo, "image/jpeg")}).json()
    without_district = client.post("/diagnose", files={"image": ("leaf.jpg", photo, "image/jpeg")}).json()
    assert with_district["probabilities"] == without_district["probabilities"]
    assert with_district["decision"] == without_district["decision"]


@pytest.mark.skipif(not config.WEIGHTS_PATH.exists(), reason="model weights not present")
def test_follow_up_is_logged_for_the_officer_and_leaves_the_diagnosis_alone():
    diagnosis = client.post("/diagnose", data={"district": "Nyanza", "season": "A"}, files={"image": ("leaf.jpg", green_leaf_jpeg(), "image/jpeg")}).json()
    reply = client.post("/follow_up", json={"diagnosis_id": diagnosis["diagnosis_id"], "answers": {"whiteflies": "Yes"}, "referral_requested": True})
    assert reply.status_code == 200 and reply.json()["guidance"]
    logged = next(row for row in client.get("/log").json() if row["id"] == diagnosis["diagnosis_id"])
    assert logged["referral_requested"] and logged["answers"] == {"whiteflies": "Yes"}
    assert logged["decision"] == diagnosis["decision"] and logged["confidence"] == diagnosis["confidence"]


def test_follow_up_for_unknown_diagnosis_is_404():
    assert client.post("/follow_up", json={"diagnosis_id": 10**9, "answers": {}}).status_code == 404


def test_every_page_is_served():
    for path in ("/", "/result", "/how-it-works", "/officer"):
        response = client.get(path)
        assert response.status_code == 200 and "<html" in response.text
