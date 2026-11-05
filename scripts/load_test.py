"""Load test: how many farmers can check a leaf at the same time, and how long each one waits.
At each level, that many simulated users send diagnoses at once, each user sending the next photo as soon as the
last answer arrives. Records the response time (median, 95th percentile, maximum), errors and diagnoses per second.

Run:  python -m scripts.load_test --base-url https://cassacheck.onrender.com --levels 1 5 10 20 --rounds 3 --out docs/testing/load_live.json
The photo is the author's own field photo api/static/samples/sample_symptoms_2.jpg (149 KB).
Every request is written to the service's case log like a real one.
"""
import argparse
import asyncio
import json
import math
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

PHOTO = Path(__file__).resolve().parent.parent / "api" / "static" / "samples" / "sample_symptoms_2.jpg"


async def user(client: httpx.AsyncClient, rounds: int, photo: bytes, timings: list, errors: list):
    for _ in range(rounds):
        started = time.perf_counter()
        try:
            response = await client.post("/diagnose", files={"image": ("leaf.jpg", photo, "image/jpeg")})
            if response.status_code == 200:
                timings.append((time.perf_counter() - started) * 1000)
            else:
                errors.append(f"HTTP {response.status_code}")
        except httpx.HTTPError as error:
            errors.append(type(error).__name__)


async def level(base_url: str, users: int, rounds: int, timeout: float) -> dict:
    photo = PHOTO.read_bytes()
    timings, errors = [], []
    limits = httpx.Limits(max_connections=users, max_keepalive_connections=users)
    async with httpx.AsyncClient(base_url=base_url, timeout=timeout, limits=limits) as client:
        started = time.perf_counter()
        await asyncio.gather(*(user(client, rounds, photo, timings, errors) for _ in range(users)))
        elapsed = time.perf_counter() - started
    ordered = sorted(timings)
    return {"users": users, "requests": users * rounds, "succeeded": len(timings), "errors": len(errors), "error_types": sorted(set(errors)),
            "median_ms": round(statistics.median(ordered)) if ordered else None,
            "p95_ms": round(ordered[math.ceil(0.95 * len(ordered)) - 1]) if ordered else None,  # nearest-rank percentile
            "max_ms": round(ordered[-1]) if ordered else None,
            "diagnoses_per_second": round(len(timings) / elapsed, 2)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--levels", type=int, nargs="+", default=[1, 5, 10, 20])
    parser.add_argument("--rounds", type=int, default=3, help="photos each simulated user sends")
    parser.add_argument("--timeout", type=float, default=60.0, help="seconds before a request counts as failed")
    parser.add_argument("--label", default="")
    parser.add_argument("--out", default=None)
    arguments = parser.parse_args()
    httpx.get(f"{arguments.base_url}/health", timeout=180)  # wake a sleeping free-plan service first
    rows = []
    for users in arguments.levels:
        row = asyncio.run(level(arguments.base_url, users, arguments.rounds, arguments.timeout))
        rows.append(row)
        print(f"{users:>3} users: {row['succeeded']}/{row['requests']} ok, median {row['median_ms']} ms, p95 {row['p95_ms']} ms, "
              f"max {row['max_ms']} ms, {row['diagnoses_per_second']} diagnoses/s, errors {row['error_types']}")
    if arguments.out:
        Path(arguments.out).parent.mkdir(parents=True, exist_ok=True)
        Path(arguments.out).write_text(json.dumps({"base_url": arguments.base_url, "label": arguments.label, "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                                   "client": platform.platform(), "photo": PHOTO.name, "rounds": arguments.rounds,
                                                   "timeout_s": arguments.timeout, "levels": rows}, indent=2))
