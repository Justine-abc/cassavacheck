# System testing and results

How CassaCheck was tested as a whole system, under what conditions, and what the numbers show. Every number below comes from a file in this folder, a notebook output or a script named next to it. Tests run on 5 November 2026 unless stated.

## 1. Test environment

| Item | Value |
|---|---|
| Laptop (client and local server) | Intel Core i7-1165G7, 8 logical cores, 6 GB RAM, Linux 7.0, Python 3.12.15, torch 2.3.1 (CPU) |
| Deployed service | Render free plan (shared CPU, 512 MB RAM), region Oregon (United States), `https://cassacheck.onrender.com`; client in Kigali, so every request crosses to the United States and back |
| Browser tests | Google Chrome 153 driven by Playwright 1.64.1, phone-sized window 390 x 844 |
| HTTP tests | httpx 0.27.0 |
| CPU limit used to imitate the free plan locally | `systemd-run --user --scope -p CPUQuota=10%` (one tenth of one core) |
| Model training and evaluation | Google Colab, T4 GPU (notebooks 01 to 07) |
| Test photos | The author's own field photos (`api/static/samples/`, Kicukiro, 31 October 2026) and generated images. No Kaggle image is used in these system tests. |

## 2. Functional requirements

| Requirement | How it is checked | Result |
|---|---|---|
| FR-01 Accept a leaf photo; check type and size | Edge cases 1 to 16 below, live and local; `test_wrong_file_type_is_rejected_with_415`, `test_corrupt_image_is_rejected_with_422` | Pass: JPEG and PNG accepted; GIF 415; over 10 MB 413; text, empty and missing file 422 |
| FR-02 District and season shown beside the result, never inside the model | Edge cases 2 and 16; `test_district_does_not_change_the_probabilities` | Pass: panel shown for a surveyed district, absent for an unknown name; probabilities identical with and without a district |
| FR-03 Calibrated probabilities for five classes | `tests/test_calibration.py` (6 tests); `/health` shows T = 1.1514 live | Pass |
| FR-04 Frozen threshold: a condition or "not sure" | `test_gate_answers_above_threshold_and_abstains_below`; blurred and tiny photos returned "not sure" (0.49) | Pass |
| FR-05 Advice or follow-up questions and referral, no chemical named | Edge cases 17 and 18; `test_advice_never_names_a_pesticide`, `test_disease_page_names_no_chemical` | Pass |
| FR-06 Anonymised case log for the extension officer | Edge cases 19 to 21; `test_follow_up_is_logged_for_the_officer_and_leaves_the_diagnosis_alone` | Pass. Live: the log was readable without a code before commit 2cc282f; after deployment with the code set, 401 without or with a wrong code |
| Access control: only officers read the log | `test_officer_log_needs_the_access_code`, `test_officer_log_is_closed_when_no_code_is_set`, `test_farmer_pages_do_not_link_to_the_officer_view` | Pass locally (401 without or with a wrong code, 503 when no code is configured) |
| Leaf check before the model | `tests/test_leaf_check.py`; edge cases 5, 7, 9, 10 | Pass |

Automated suite: 29 tests (`python3 -m pytest --verbose`), all passing.

## 3. Edge cases, end to end over HTTP

`python -m scripts.edge_case_tests --base-url <address>`. Raw results: `edge_cases_local.json`, `edge_cases_live.json`. Live column: the version deployed before the fixes (`edge_cases_live.json`); the same cases after the fixes are in `edge_cases_live_after_fix.json`, with every diagnosis answer unchanged and JPEG diagnoses taking 0.5 to 1.3 s. Live times include the trip from Kigali to the server (about 0.4 s for a request that does no work, such as the GIF case).

| # | Input | Expected | Local result | Live result (time) |
|---|---|---|---|---|
| 1 | Normal field photo (JPEG) | A condition or "not sure" | CGM 0.95 | CGM 0.95 (8.8 s) |
| 2 | Same photo with district and season | Same answer, panel shown | CGM 0.95, panel | CGM 0.95, panel (6.9 s) |
| 3 | Field photo as PNG | Accepted | healthy 0.93 | healthy 0.93 (7.8 s) |
| 4 | Photo rotated 90 degrees | Accepted | CGM 0.97 | CGM 0.97 (5.2 s) |
| 5 | Very dark photo (10% brightness) | Refused or "not sure" | Refused by leaf check | Refused (1.5 s) |
| 6 | Blurred photo (Gaussian radius 8) | "Not sure" or answer | Not sure, 0.49 | Not sure, 0.49 (5.8 s) |
| 7 | Black and white photo | Refused (no plant colour) | Refused | Refused (0.9 s) |
| 8 | Tiny image, 16 x 12 pixels | Accepted | Not sure, 0.49 | Not sure, 0.49 (3.8 s) |
| 9 | Plain grey image | Refused | Refused | Refused (0.4 s) |
| 10 | Random noise | Refused | Refused | Refused (1.1 s) |
| 11 | File over 10 MB | 413 | 413 | 413 (15.7 s, the upload itself) |
| 12 | Text file sent as a photo | 422 | 422 | 422 |
| 13 | Empty file | 422 | 422 | 422 |
| 14 | GIF | 415 | 415 | 415 (0.4 s) |
| 15 | No photo | 422 | 422 | 422 |
| 16 | Unknown district name | Answer, no panel | CGM 0.95, no panel | CGM 0.95, no panel |
| 17 | Follow-up answers with referral | 200 with guidance | 200 | 200 |
| 18 | Follow-up for an unknown case | 404 | 404 | 404 |
| 19 | Officer log without a code | 401 | 401 | Before 2cc282f: **200 (open)**. Deployed, before the code was set: 503 (closed). With the code set on Render: 401 |
| 20 | Officer log with a wrong code | 401 | 401 | Before: 200 (open). With the code set: 401 |
| 21 | Officer log with the right code | 200 | 200 | 200: checked by the author in the browser on 5 Nov; the code is not written in any file |

What this shows: the blurred and tiny photos were not given a confident wrong answer; the gate said "not sure". The dark and black and white photos were stopped before the model. Weak spot: the tiny 16 x 12 image passed the leaf check because it is green; the leaf check measures colour only.

## 4. Speed

| Measure | Result | Source |
|---|---|---|
| Model forward pass, one CPU thread, median of 100 | 19.8 ms (MobileNetV3-Large); ResNet-18 61.7 ms | `scripts/measure_latency.py`, README |
| Same, re-run 5 Nov while a browser test ran on the same laptop | 21.0 ms; ResNet-18 63.9 ms | `scripts/measure_latency.py` |
| Live service waking from sleep (first request after idle) | 82.8 s | `curl` on `/health`, 5 Nov |
| Live diagnosis, one user, before the thread fix | median 5.7 s (2 requests); 3.8 to 8.8 s in the edge-case run | `load_live_before_fix.json`, `edge_cases_live.json` |
| Live diagnosis, one user, after the thread fix (commit d987f0b) | median 0.9 s (3 requests); 0.5 to 1.3 s for JPEG photos in the edge-case run | `load_live_after_fix.json`, `edge_cases_live_after_fix.json` |

**Problem found and fixed.** The live diagnosis took seconds although the model needs 20 ms. Under a 10% CPU cap on the laptop, the model took a median of 8,550 ms per photo with PyTorch's default of 4 threads and 504 ms with 1 thread (25% cap: 898 ms and 197 ms). Several threads compete for a fraction of one CPU. The server now sets one thread (`CASSACHECK_TORCH_THREADS`, default 1, `api/config.py`). On all 27 field and sample photos the logits changed by at most 0.000004 and every answer or "not sure" stayed the same.

## 5. Load: users at the same time

`python -m scripts.load_test --base-url <address> --levels 1 5 10 20`. Each simulated user sends the next photo as soon as the last answer arrives (149 KB field photo). A request fails after 60 s.

| Setup | Users | Succeeded | Median | 95th percentile | Diagnoses per second |
|---|---|---|---|---|---|
| Live, deployed version (4 threads) | 1 | 2 of 2 | 5,710 ms | 5,889 ms | 0.18 |
| | 5 | 9 of 10 | 12,800 ms | 33,671 ms | 0.24 |
| | 10 | 7 of 20 | 18,415 ms | 29,273 ms | 0.23 |
| Live, after the fix (1 thread, d987f0b) | 1 | 3 of 3 | 894 ms | 1,459 ms | 0.93 |
| | 5 | 15 of 15 | 1,560 ms | 2,970 ms | 2.50 |
| | 10 | 30 of 30 | 2,566 ms | 4,953 ms | 3.03 |
| | 20 | 60 of 60 | 2,411 ms | 12,120 ms | 3.50 |
| Local, 10% CPU cap, 4 threads | 1 | 2 of 2 | 10,893 ms | 13,387 ms | 0.09 |
| | 5 | 10 of 10 | 32,951 ms | 57,884 ms | 0.11 |
| | 10 | 6 of 20 | 30,583 ms | 56,982 ms | 0.05 |
| Local, 10% CPU cap, 1 thread (fix) | 1 | 3 of 3 | 901 ms | 2,392 ms | 0.73 |
| | 5 | 15 of 15 | 2,794 ms | 9,983 ms | 1.09 |
| | 10 | 30 of 30 | 8,151 ms | 10,088 ms | 1.11 |
| | 20 | 60 of 60 | 16,796 ms | 17,998 ms | 1.12 |

Raw results: `load_live_before_fix.json`, `load_live_after_fix.json`, `load_local_cap10_threads4.json`, `load_local_cap10_threads1.json`. Live failures were HTTP 502 from Render; local failures were 60 s timeouts.

Reading: with one thread, a tenth of a CPU serves about 1.1 diagnoses per second, ten times more than before, and no request failed up to 20 users. Photos queue, so waiting grows with the number of users: the median stays under 3 s up to about 5 users at once. On the live service the fix took one diagnosis from 5.7 s to 0.9 s, and all 60 requests from 20 simultaneous users succeeded with a median of 2.4 s, where before the fix 13 of 20 requests failed at 10 users. The 95th percentile at 20 users (12.1 s) shows that some users still wait while photos queue. For more users, a paid instance with a full CPU is the step; the code does not change.

## 6. Network conditions

`python -m scripts.network_test --base-url http://localhost:8000 --channel chrome --runs 2`. Real browser, phone-sized window, network slowed in Chrome with the values of its presets (Fast 3G: 562.5 ms latency, 1.44 Mbit/s down, 675 kbit/s up; Slow 3G: 2,000 ms latency, 400 kbit/s both ways). The server ran on the laptop so that only the network is measured; the live service adds its own processing time and the distance to Render. Each run is a first visit with an empty cache; the cache is then on, as in a normal browser, for the result page. Medians of 2 runs. Raw results: `network_local.json`.

| Photo | Network | Open the page (first visit) | Send photo and get the answer | Press "Diagnose" to result shown |
|---|---|---|---|---|
| Field photo, 149 KB | No throttling | 2.5 s | 0.13 s | 0.36 s |
| | Fast 3G | 13.1 s | 2.4 s | 3.2 s |
| | Slow 3G | 45.8 s | 5.1 s | 7.5 s |
| Field photo, 459 KB | No throttling | 2.6 s | 0.19 s | 0.43 s |
| | Fast 3G | 14.5 s | 6.2 s | 7.1 s |
| | Slow 3G | 45.9 s | 11.5 s | 14.0 s |
| Field photo enlarged to 4000 x 3000 (1,712 KB, the size of a phone camera photo) | No throttling | 2.6 s | 0.34 s | 0.64 s |
| | Fast 3G | 13.1 s | 21.4 s | 22.4 s |
| | Slow 3G | 45.9 s | 37.1 s | 39.7 s |

No network: the page shows "No connection to the server. Check your internet and try again." and the Diagnose button can be pressed again. Nothing works offline; the model runs only on the server.

Two problems this shows:

1. **The first visit downloads 1.93 MB.** The largest file is the icon font (1,114 KB, the whole Material Symbols set although the pages use about 30 icons), then the three sample photos (517 KB together) and the Tailwind script (128 KB). On Fast 3G opening the page takes 13 s. Possible fixes: request only the icons used (Google Fonts `icon_names`), smaller sample thumbnails, and a prebuilt stylesheet instead of the Tailwind script.
2. **The photo is sent at full size.** The time to an answer grows with the file: 2.4 s for 149 KB but 21.4 s for a phone-sized photo on Fast 3G. The model only uses 224 x 224 pixels, so shrinking the photo on the phone before sending (for example to 800 x 600, the size of the training images) would keep every upload near the 149 KB case.

## 7. Model evaluation

Internal test (3,210 images, read only after the model, temperature and threshold were frozen; notebook 04b, run twice with identical code and frozen values, results equal to the fourth decimal). MobileNetV3-Large, seed 1, T = 1.1514, threshold 0.6752.

| Class | Precision | Recall (sensitivity) | F1 | Images |
|---|---|---|---|---|
| CBB | 0.4599 | 0.6646 | 0.5436 | 164 |
| CBSD | 0.7591 | 0.7012 | 0.7290 | 328 |
| CGM | 0.7294 | 0.7927 | 0.7597 | 357 |
| CMD | 0.9629 | 0.9078 | 0.9346 | 1,974 |
| healthy | 0.6295 | 0.6848 | 0.6559 | 387 |
| Macro average | 0.7081 | 0.7502 | 0.7246 | 3,210 |

Accuracy 0.8346 (95% bootstrap interval 0.8212 to 0.8474); macro-F1 0.7246 (0.705 to 0.7449); ECE with 15 bins 0.0294 before and 0.0116 after temperature scaling; coverage 0.7922; accuracy on answered photos 0.9162 (0.9044 to 0.9265); accuracy on the photos it declined 0.5232. Majority baseline ("always CMD"): accuracy 0.615, macro-F1 0.1523.

Figures: `figures/test_confusion_mobilenetv3_seed1.png`, `figures/test_reliability_riskcoverage_mobilenetv3_seed1.png` (both from notebook 04b), `figures/training_curves_nb03.png` (from the printed logs of notebook 03: training loss falls for all 8 epochs while validation macro-F1 stops improving after about epoch 5; the deployed checkpoint is epoch 5, the best validation macro-F1, 0.7439).

External test, Ghana (CCMT, 6,027 images, notebook 05): accuracy 0.6187, macro-F1 over the 4 shared classes 0.6659, ECE 0.1595 before and 0.1269 after, coverage 0.6441, accuracy on answered 0.7439.

## 8. Results against the objectives (proposal targets)

| Objective | Target | Result | Met? |
|---|---|---|---|
| Classification quality | Macro-F1 at least 0.85 | 0.7246 (internal test, macro average) | No |
| Calibration | ECE at least halved on both test sets | Internal 0.0294 to 0.0116 (halved); Ghana 0.1595 to 0.1269 (not halved) | Internal yes, Ghana no |
| Abstention | Accuracy on answered at least 0.95 at about 80% coverage | 0.9162 at 0.7922 | No |
| Speed of the model | Under 100 ms, batch 1, one CPU core, median of 100 | 19.8 ms | Yes |
| End to end | Under 3 s on 3G | Fast 3G, local server: answer in 2.4 s for a 149 KB photo, but 6.2 s for 459 KB and 21.4 s for a phone-sized photo; first page visit 13.1 s | No (met only for small photos) |
| Safety of advice | No chemical or dose named | Enforced by two tests | Yes |
| Privacy | No photos, names or phone numbers stored; officer-only log | Checked by tests and edge cases 19 to 21 (local) | Yes (local and live) |

## 9. Not tested

- No usability test with farmers or extension officers took place. The interface has not been tried by its intended users; this is the first step for future work.
- No labelled Rwandan photos: on the author's 24 field photos only the model's behaviour can be described, not its accuracy.
- Load beyond 20 simultaneous users, and real phones on a real 3G network (network speeds here are emulated in Chrome).

## 10. Reproduce

```bash
python3 -m pytest --verbose
python3 -m scripts.measure_latency --runs 100
python -m scripts.edge_case_tests --base-url https://cassacheck.onrender.com --out docs/testing/edge_cases_live.json
python -m scripts.load_test --base-url https://cassacheck.onrender.com --levels 1 5 10 20 --rounds 3 --out docs/testing/load_live.json
pip install playwright && python -m playwright install chromium
python -m scripts.network_test --base-url http://localhost:8000 --runs 2 --out docs/testing/network_local.json
```
