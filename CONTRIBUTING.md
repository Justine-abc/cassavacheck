# Contributing to CassaCheck

These rules protect the research design behind the product. Changes that break them are not accepted, however small.

## Design constraints
- Five classes only: CBB, CBSD, CGM, CMD, healthy. No other condition is ever predicted, displayed or logged.
- District information is shown beside the result. It is never an input to the model and never changes the probabilities.
- The calibration temperature and the abstention threshold are read from `models/calibration.json`. They are fitted once in `notebooks/04_calibration_abstention.ipynb` on validation data and are never recomputed in the API.
- The test split (`data/split_v1_seed42.csv`, rows with `split == "test"`) is never read by training, calibration or model-selection code. It is reserved for the final evaluation.
- Advice text never names a pesticide, fungicide, insecticide or dose. `tests/test_districts_and_advice.py` enforces this; keep that test passing.
- No image bytes, coordinates or personal data are stored. The log holds district, season, decision, confidence, a timestamp and, when given, the farmer's answers to the follow-up questions (fixed options only, never free text).

## Code conventions
- Python: FastAPI for the API; one responsibility per module (`api/classifier.py`, `calibration.py`, `districts.py`, `advice.py`, `log_store.py`); `api/main.py` holds routes only.
- Full variable names, no abbreviations; long-form command-line flags in documentation and scripts.
- Comments explain why, not what.
- Frontend: the screens designed in `docs/design/` are built as static pages in `api/static/` (diagnose, result, how it works, officer view), styled with the design's Tailwind tokens in `theme.js` and served by FastAPI. Pages only call the API; no diagnosis logic runs in the browser.
- Do not add features beyond the proposal's FR-01 to FR-06 without a note in the scope table of the technical report.

## Before opening a pull request
```bash
python3 -m pytest --verbose
python3 scripts/measure_latency.py --runs 100
```
Both must run clean, and the latency line goes into the pull request description.
