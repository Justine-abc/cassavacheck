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
