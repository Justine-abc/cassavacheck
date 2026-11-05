"""End-to-end edge-case checks against a running CassaCheck service (local or deployed).
Each case sends one request over HTTP, as a phone would, and records the expected and the actual outcome.

Run:  python -m scripts.edge_case_tests --base-url https://cassacheck.onrender.com --out docs/testing/edge_cases_live.json
      python -m scripts.edge_case_tests --base-url http://localhost:8000 --officer-code <code> --out docs/testing/edge_cases_local.json
Test photos are the author's own field photos in api/static/samples/; every other input is generated here.
"""
import argparse
import io
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import numpy as np
from PIL import Image, ImageFilter

SAMPLES = Path(__file__).resolve().parent.parent / "api" / "static" / "samples"


def jpeg(image: Image.Image, quality: int = 90) -> bytes:
    buffer = io.BytesIO(); image.save(buffer, format="JPEG", quality=quality); return buffer.getvalue()


def png(image: Image.Image) -> bytes:
    buffer = io.BytesIO(); image.save(buffer, format="PNG"); return buffer.getvalue()


def build_cases():
    leaf = Image.open(SAMPLES / "sample_symptoms_2.jpg").convert("RGB")
    healthy = Image.open(SAMPLES / "sample_looks_healthy.jpg").convert("RGB")
    noise = Image.fromarray(np.random.default_rng(0).integers(0, 256, (2400, 1800, 3), dtype=np.uint8))
    answer = "200: a condition or not sure"
    return [
        # (name, what it checks, files, form data, expected)
        ("Normal field photo (JPEG)", "FR-01, FR-03, FR-04", ("leaf.jpg", jpeg(leaf), "image/jpeg"), {}, answer),
        ("Same photo with district and season", "FR-02: district shown, diagnosis unchanged", ("leaf.jpg", jpeg(leaf), "image/jpeg"), {"district": "Nyanza", "season": "A"}, answer),
        ("Field photo as PNG", "FR-01: second accepted type", ("leaf.png", png(healthy), "image/png"), {}, answer),
        ("Photo rotated 90 degrees", "Robustness: phone held sideways", ("leaf.jpg", jpeg(leaf.rotate(90, expand=True)), "image/jpeg"), {}, answer),
        ("Very dark photo (10% brightness)", "Robustness: evening light", ("leaf.jpg", jpeg(Image.eval(leaf, lambda v: int(v * 0.1))), "image/jpeg"), {}, "422 refused or not sure"),
        ("Blurred photo (Gaussian radius 8)", "Robustness: shaking hand", ("leaf.jpg", jpeg(leaf.filter(ImageFilter.GaussianBlur(8))), "image/jpeg"), {}, "not sure or answer"),
        ("Black and white photo", "Robustness: colour lost", ("leaf.jpg", jpeg(leaf.convert("L").convert("RGB")), "image/jpeg"), {}, "422 refused (no plant colour)"),
        ("Tiny image (16 x 12 pixels)", "Edge: very small input", ("leaf.jpg", jpeg(leaf.resize((16, 12))), "image/jpeg"), {}, answer),
        ("Plain grey image", "Leaf check: not a plant", ("grey.jpg", jpeg(Image.new("RGB", (800, 600), (128, 128, 128))), "image/jpeg"), {}, "422 refused"),
        ("Random noise image", "Leaf check: not a plant", ("noise.jpg", jpeg(noise.resize((800, 600))), "image/jpeg"), {}, "422 refused"),
        ("File over 10 MB", "FR-01: size limit", ("big.png", png(noise), "image/png"), {}, "413 too large"),
        ("Text file sent as a photo", "FR-01: corrupt file", ("leaf.jpg", b"this is not an image", "image/jpeg"), {}, "422 unreadable"),
        ("Empty file", "FR-01: empty upload", ("leaf.jpg", b"", "image/jpeg"), {}, "422 unreadable"),
        ("GIF file", "FR-01: wrong type", ("leaf.gif", b"GIF89a", "image/gif"), {}, "415 wrong type"),
        ("No photo at all", "FR-01: missing field", None, {}, "422 missing"),
        ("Unknown district name", "FR-02: bad district text", ("leaf.jpg", jpeg(leaf), "image/jpeg"), {"district": "Atlantis", "season": "A"}, "200, no district panel"),
    ]


def summarise(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text[:80]
    if response.status_code == 200 and "decision" in body:
        panel = "with district panel" if body.get("district_panel") else "no district panel"
        return f"{body['decision']} {body['confidence']:.2f}, {panel}"
    detail = body.get("detail")
    return (detail if isinstance(detail, str) else json.dumps(detail))[:90]


def run(base_url: str, officer_code: str | None) -> list[dict]:
    results = []
    with httpx.Client(base_url=base_url, timeout=120) as client:
        client.get("/health")  # wake a sleeping free-plan service before timing anything
        for name, checks, file, data, expected in build_cases():
            started = time.perf_counter()
            response = client.post("/diagnose", files={"image": file} if file else None, data=data)
            results.append({"case": name, "checks": checks, "expected": expected, "status": response.status_code,
                            "actual": summarise(response), "ms": round((time.perf_counter() - started) * 1000)})
        # Follow-up and officer access
        diagnosis = client.post("/diagnose", files={"image": ("leaf.jpg", (SAMPLES / "sample_symptoms_1.jpg").read_bytes(), "image/jpeg")}).json()
        for name, checks, call, expected in [
            ("Follow-up answers and referral", "FR-05", lambda: client.post("/follow_up", json={"diagnosis_id": diagnosis["diagnosis_id"], "answers": {"whiteflies": "Yes"}, "referral_requested": True}), "200 with guidance"),
            ("Follow-up for a case that does not exist", "FR-05: bad id", lambda: client.post("/follow_up", json={"diagnosis_id": 10**9, "answers": {}}), "404"),
            ("Officer log without the access code", "Access control", lambda: client.get("/log"), "401"),
            ("Officer log with a wrong code", "Access control", lambda: client.get("/log", headers={"X-Officer-Code": "wrong-code"}), "401"),
        ] + ([("Officer log with the right code", "FR-06, access control", lambda: client.get("/log", headers={"X-Officer-Code": officer_code}), "200, case listed")] if officer_code else []):
            started = time.perf_counter(); response = call()
            try:
                body = response.json()
                actual = (f"{len(body)} cases" if isinstance(body, list) else (body.get("detail") or ", ".join(body.get("guidance", []))[:60]))
            except ValueError:
                actual = response.text[:60]
            results.append({"case": name, "checks": checks, "expected": expected, "status": response.status_code,
                            "actual": str(actual)[:90], "ms": round((time.perf_counter() - started) * 1000)})
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--officer-code", default=None)
    parser.add_argument("--out", default=None)
    arguments = parser.parse_args()
    rows = run(arguments.base_url, arguments.officer_code)
    for row in rows:
        print(f"{row['status']:>4}  {row['ms']:>6} ms  {row['case']:<42} expected: {row['expected']:<34} actual: {row['actual']}")
    if arguments.out:
        Path(arguments.out).parent.mkdir(parents=True, exist_ok=True)
        Path(arguments.out).write_text(json.dumps({"base_url": arguments.base_url, "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                                   "client": platform.platform(), "results": rows}, indent=2))
