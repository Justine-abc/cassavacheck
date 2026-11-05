"""End-to-end timing in a real browser under slower networks: open the diagnose page, choose a photo, press
"Diagnose leaf", wait until the result page shows the answer. Also checks what the farmer sees when the network is gone.

Network profiles use the values of the Chrome DevTools presets (Chrome applies them per request):
  Fast 3G: 562.5 ms latency, 1.44 Mbit/s down, 675 kbit/s up.   Slow 3G: 2,000 ms latency, 400 kbit/s down and up.
Each run uses a fresh browser profile, so the first page load has nothing cached (a first visit). The cache is then
switched on, as in a normal browser, before the photo is sent, so the result page reuses the files already downloaded.

Needs Playwright (pip install playwright; python -m playwright install chromium) or Google Chrome (--channel chrome).
Run:  python -m scripts.network_test --base-url https://cassacheck.onrender.com --photo api/static/samples/sample_symptoms_2.jpg --runs 3 --out docs/testing/network_live.json
"""
import argparse
import json
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

PROFILES = {
    "No throttling": None,
    "Fast 3G": {"latency": 562.5, "downloadThroughput": 1_440_000 / 8, "uploadThroughput": 675_000 / 8},
    "Slow 3G": {"latency": 2000, "downloadThroughput": 400_000 / 8, "uploadThroughput": 400_000 / 8},
}


def one_run(browser, base_url: str, photo: Path, profile: dict | None) -> dict:
    context = browser.new_context(viewport={"width": 390, "height": 844})
    page = context.new_page()
    session = context.new_cdp_session(page)
    session.send("Network.enable")
    session.send("Network.setCacheDisabled", {"cacheDisabled": True})
    received = {"bytes": 0}
    urls, sizes = {}, {}
    session.on("Network.requestWillBeSent", lambda event: urls.__setitem__(event["requestId"], event["request"]["url"]))
    def finished(event):
        received["bytes"] += event.get("encodedDataLength", 0)
        sizes[urls.get(event["requestId"], "?")] = event.get("encodedDataLength", 0)
    session.on("Network.loadingFinished", finished)
    if profile:
        session.send("Network.emulateNetworkConditions", {"offline": False, **profile})
    started = time.perf_counter()
    page.goto(f"{base_url}/", wait_until="load", timeout=180_000)
    page.wait_for_selector("[data-sample]", timeout=180_000)  # page usable: samples and buttons drawn
    page_ms = (time.perf_counter() - started) * 1000
    page_kb = received["bytes"] / 1024
    largest = sorted(((round(size / 1024), url.split("?")[0]) for url, size in sizes.items()), reverse=True)[:6]
    session.send("Network.setCacheDisabled", {"cacheDisabled": False})
    page.set_input_files("#photo-input", str(photo))
    started = time.perf_counter()
    with page.expect_response(lambda response: response.url.endswith("/diagnose"), timeout=180_000) as answer:
        page.click("#diagnose-button")
    answer.value.finished()
    api_ms = (time.perf_counter() - started) * 1000
    page.wait_for_url("**/result", timeout=180_000)
    page.wait_for_selector("#right-column", timeout=180_000)  # answer drawn on the result page
    diagnose_ms = (time.perf_counter() - started) * 1000
    context.close()
    return {"page_ms": page_ms, "page_kb": page_kb, "api_ms": api_ms, "diagnose_ms": diagnose_ms, "largest": largest}


def offline_check(browser, base_url: str, photo: Path) -> str:
    context = browser.new_context(viewport={"width": 390, "height": 844})
    page = context.new_page()
    page.goto(f"{base_url}/", wait_until="load", timeout=180_000)
    page.wait_for_selector("[data-sample]")
    page.set_input_files("#photo-input", str(photo))
    context.set_offline(True)
    page.click("#diagnose-button")
    page.wait_for_selector("#error-box:not(.hidden)", timeout=30_000)
    message = page.inner_text("#error-box")
    enabled_again = page.is_enabled("#diagnose-button")
    context.close()
    return f"{message} (button usable again: {enabled_again})"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--photo", type=Path, nargs="+", default=[Path("api/static/samples/sample_symptoms_2.jpg")])
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--channel", default=None, help="'chrome' to use the installed Google Chrome")
    parser.add_argument("--label", default="")
    parser.add_argument("--out", default=None)
    arguments = parser.parse_args()
    rows = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=arguments.channel)
        for photo in arguments.photo:
            for name, profile in PROFILES.items():
                runs = [one_run(browser, arguments.base_url, photo, profile) for _ in range(arguments.runs)]
                row = {"photo": photo.name, "photo_kb": round(photo.stat().st_size / 1024), "network": name, "runs": arguments.runs,
                       "page_load_ms_median": round(statistics.median(r["page_ms"] for r in runs)),
                       "page_kb_median": round(statistics.median(r["page_kb"] for r in runs)),
                       "upload_and_answer_ms_median": round(statistics.median(r["api_ms"] for r in runs)),
                       "diagnose_ms_median": round(statistics.median(r["diagnose_ms"] for r in runs)),
                       "diagnose_ms_max": round(max(r["diagnose_ms"] for r in runs)), "largest_files_kb": runs[0]["largest"]}
                rows.append(row)
                print(f"{photo.name} ({row['photo_kb']} KB) | {name:<13} | page {row['page_load_ms_median']} ms ({row['page_kb_median']} KB) | "
                      f"upload+answer {row['upload_and_answer_ms_median']} ms | press to result shown {row['diagnose_ms_median']} ms", flush=True)
        offline = offline_check(browser, arguments.base_url, arguments.photo[0])
        print("Offline:", offline)
        browser.close()
    if arguments.out:
        Path(arguments.out).parent.mkdir(parents=True, exist_ok=True)
        Path(arguments.out).write_text(json.dumps({"base_url": arguments.base_url, "label": arguments.label, "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                                   "client": platform.platform(), "profiles": PROFILES, "results": rows, "offline": offline}, indent=2))
