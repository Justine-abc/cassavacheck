# CassaCheck: Technical Report (maximum 5 pages)

Author: Justine Umuhoza. Repository: https://github.com/Justine-abc/cassavacheck. Video: VIDEO_LINK.

## 1. Scope alignment and feature validation (1 page)

| Planned feature (proposal) | Intended purpose | Current status | Evidence |
|---|---|---|---|
| FR-01 Accept a leaf photo from a mobile browser; validate type and size | Input to the diagnosis without any location or personal data | Completed | `api/main.py` `/diagnose`: 415 on wrong type, 413 over 10 MB, 422 on a corrupt file; `tests/test_api.py` |
| FR-02 District and season chosen from lists; published incidence shown separately with survey year and number of fields | Site information beside the result, never inside the model | Completed for the two districts verified from the 2019 survey; remaining 11 districts and the CMD column to be added from the same paper | `api/districts.py`, `data/district_prevalence.csv`, panel screenshot |
| FR-03 Calibrated probabilities for the five classes | Honest confidence | Completed; temperature 0.93 fitted on a validation half | `api/calibration.py` `Calibrator`, `models/calibration.json`, `notebooks/04_calibration_abstention.ipynb` |
| FR-04 Frozen abstention threshold; label or abstention | Say "not sure" instead of guessing | Completed; threshold 0.6455 at target coverage 0.80, realized coverage 0.79 | `AbstentionGate`, risk-coverage figure |
| FR-05 Result card with advice or three follow-up questions and referral | Management advice, never a pesticide | Completed | `api/advice.py`, `api/static/index.html`, `tests/test_districts_and_advice.py` |
| FR-06 Anonymised log (district, season, decision, confidence) | Evaluation and officer view | Completed with SQLite; PostgreSQL on Render planned | `api/log_store.py`, `/log` endpoint |
| Near-duplicate detection and published 70/15/15 split | Prevent leakage | Completed; zero fingerprint collisions at hash size 8 | `notebooks/01_data_and_split.ipynb`, `data/split_v1_seed42.csv` |
| MobileNetV3-Large and ResNet-18 baselines, five seeds | Compare backbones with uncertainty | Partial: MobileNetV3-Large one seed, two epochs (validation accuracy 0.8237, macro-F1 0.7109); ResNet-18 class implemented, not yet trained; five seeds planned by 2 November | `api/classifier.py`, `notebooks/02_baseline_train.ipynb` |
| External evaluation on CCMT, once, with class mapping | Cross-country transfer | Not implemented yet; planned by 9 November, protocol fixed in the proposal (Table 5) | proposal section 3.2.4 |
| React web interface from the Stitch designs | Mobile-first UI | Partial: designs complete and exported; current interface is one static page implementing the same flow | `docs/design/*.html`, Figma link |
| Deployment on Render and Vercel | Public demonstration | Not yet; runs locally with one command | `README.md` |

Justification of deviations: the course deadline for this version (23 October) came before the proposal's phases 2 to 4; the calibrated, abstaining five-class classifier and the demonstration are complete, the multi-seed comparison and the external evaluation remain scheduled.

## 2. Technical functionality (1 page)
Backend/frontend interaction: the page posts a multipart form (image, district, season) to `/diagnose`; the API returns one JSON object with the decision, calibrated probabilities, threshold, advice, follow-up questions and the district sentence; the page renders the confident or the not-sure state from that one response.
Data handling: image validated by content type, size and decodability; preprocessed to 224x224; never stored. District table loaded once from CSV. Log row written per request without image bytes or coordinates.
Logic: logits from the classifier; temperature scaling; abstention gate; advice rules; district lookup with season fallback.

## 3. Algorithms and problem solving (1 page)
- Perceptual-hash near-duplicate detection and stratified group split (notebook 01): why, how, result (0 collisions, every class in every split).
- Class-weighted cross-entropy for the 61% CMD imbalance (notebook 02): effect on CBB and CBSD recall.
- Temperature scaling fitted by L-BFGS on validation logits (notebook 04): T = 0.93; ECE 0.0275 before, 0.0296 after on the other half; interpretation: the two-epoch model is not over-confident, so calibration is neutral here and is retained for the fully trained models.
- Abstention threshold as the 20th percentile of calibrated confidence on the fit half: realized coverage 0.791; accuracy 0.907 on retained against 0.825 overall; 0.513 on abstained leaves, which shows the gate selects the hard cases.
- Expected calibration error and risk-coverage curve implemented from their definitions (equations in the proposal).

## 4. Testing approaches and results (1 page)
Strategy 1, unit testing (pytest, 11 tests): calibration math, gate behaviour, settings fallback, district lookup and fallback, forbidden-word check on advice. Why: these are the decision rules; they must be right independent of any model. Results: all pass. Improvement made: the gate originally accepted a threshold of 1.5; a validation and a test were added.
Strategy 2, integration testing (FastAPI TestClient): health, districts, 415 on text upload, 422 on a corrupt image, full diagnosis with schema checks and the abstain/threshold consistency rule. Results: all pass with weights present.
Strategy 3, functional testing with different inputs (video): a dataset leaf, a field photo from Kigali, a non-leaf photo, a PNG, a text file, a 12 MB image. Expected behaviour and observed responses tabulated.
Strategy 4, performance: `scripts/measure_latency.py`, forward pass at batch size 1, one thread, median of 100 runs: FILL ms on the laptop CPU (FILL model), FILL ms on a phone-class device if available; end-to-end request in the browser: FILL s on Wi-Fi, FILL s on mobile data.
Compatibility: Chrome and Firefox on Ubuntu; Chrome on Android over the local network (phone to laptop IP); note any layout or upload differences.

## 5. Code quality practices (half a page)
Separation of concerns: six modules, one responsibility each, matching the class diagram of the proposal (ImageClassifier, Calibrator, AbstentionGate, Decision, DistrictRepository, AdvisoryService, DiagnosisLog). Abstraction and inheritance: `ImageClassifier` is an abstract base; `MobileNetV3Classifier` and `ResNet18Classifier` implement `build_network`; the API depends only on the base. Encapsulation: frozen dataclasses for `Decision`, `CalibrationSettings`, `DistrictPrevalence`; tuned values live in `calibration.json`, never in code. Polymorphism: any classifier subclass is interchangeable at start-up. Data as rules: advice and questions are data structures, with a test that forbids chemical names. Naming: full words, long-form CLI flags, comments that explain why. Routes contain no logic.

## 6. Limitations and next steps (quarter page)
One seed, two epochs; calibration neutral at this stage; two districts; external evaluation and deployment scheduled; React build from the completed designs after the external evaluation.
