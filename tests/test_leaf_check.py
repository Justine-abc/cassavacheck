"""The input check refuses photos with almost no plant colour and lets green and yellow leaves through."""
import io

from fastapi.testclient import TestClient
from PIL import Image

from api import main
from api.leaf_check import LeafCheck, plant_fraction


def solid(colour) -> Image.Image:
    return Image.new("RGB", (320, 240), colour)


def test_green_and_yellow_leaves_count_as_plant_grey_and_white_do_not():
    assert plant_fraction(solid((60, 140, 50))) == 1.0      # green leaf
    assert plant_fraction(solid((200, 190, 60))) == 1.0     # yellow mosaic leaf
    assert plant_fraction(solid((128, 128, 128))) == 0.0    # grey wall
    assert plant_fraction(solid((250, 250, 250))) == 0.0    # white screenshot


def test_missing_file_disables_the_check(tmp_path):
    check = LeafCheck.load(tmp_path / "absent.json")
    assert check.min_plant_fraction == 0.0 and check.looks_like_leaf(solid((128, 128, 128)))


def test_api_refuses_a_non_leaf_before_the_model_and_logs_nothing(monkeypatch):
    monkeypatch.setattr(main, "leaf_check", LeafCheck(min_plant_fraction=0.1, fitted_on="test"))
    client = TestClient(main.app)
    before = len(client.get("/log?limit=200").json())
    buffer = io.BytesIO()
    solid((128, 128, 128)).save(buffer, format="JPEG")
    response = client.post("/diagnose", files={"image": ("wall.jpg", buffer.getvalue(), "image/jpeg")})
    assert response.status_code in (422, 503)   # 503 only when weights are absent on the test machine
    if response.status_code == 422:
        assert "leaf" in response.json()["detail"]
    assert len(client.get("/log?limit=200").json()) == before
