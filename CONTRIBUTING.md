# Contributing to CassaCheck

These rules protect the research design behind the product. Changes that break them are not accepted, however small.

## Design constraints
- Five classes only: CBB, CBSD, CGM, CMD, healthy. No other condition is ever predicted, displayed or logged.
- District information is shown beside the result. It is never an input to the model and never changes the probabilities.
- The calibration temperature and the abstention threshold are read from `models/calibration.json`. They are fitted once in `notebooks/04_calibration_abstention.ipynb` on validation data and are never recomputed in the API.
- The test split (`data/split_v1_seed42.csv`, rows with `split == "test"`) is never read by training, calibration or model-selection code. It is reserved for the final evaluation.
- Advice text never names a pesticide, fungicide, insecticide or dose. `tests/test_districts_and_advice.py` enforces this; keep that test passing.
- No image bytes or coordinates are stored. The log holds district, season, decision, confidence, a timestamp and, when given, the farmer's answers to the follow-up questions (fixed options only, never free text from the farmer).
- The only personal data is a phone number on a referred case, stored only when the farmer ticked consent. It is never returned to a farmer page or included in the CSV export, and it is deleted when the case is answered or after `CONTACT_RETENTION_DAYS` in `api/log_store.py`. The officer's note is shown to the farmer, so it follows the advice rule (no chemical, no dose); the API refuses a note that breaks it.
- Every farmer page works in English and Kinyarwanda. Visible text goes through `T()` or carries `data-t`, with its Kinyarwanda in `api/static/i18n.js`; `tests/test_translations.py` fails on a missing entry. Values sent to the API stay in English.

## Code conventions
- Python: FastAPI for the API; one responsibility per module (`api/classifier.py`, `calibration.py`, `districts.py`, `advice.py`, `log_store.py`); `api/main.py` holds routes only.
- Full variable names, no abbreviations; long-form command-line flags in documentation and scripts.
- Comments explain why, not what.
- Frontend: the screens designed in `docs/design/` are built as static pages in `api/static/` (diagnose, result, how it works, diseases, officer view), styled with the design's Tailwind tokens in `theme.js` and served by FastAPI. Pages only call the API; no diagnosis logic runs in the browser. Motion lives in `app.css` and is switched off under reduced motion. When `app.css`, `theme.js`, `app.js` or the favicon change, raise the `?v=` number on their links in every page so browsers fetch the new copy. Sample photos in `api/static/samples/` are the author's own field photos and carry no disease label. Who sees what: farmers use the diagnose, result, my case, how it works and diseases pages without an account (my case needs the case number and check code); the case log (`/log`, `/officer`) is for extension officers only and needs the access code from the `CASSACHECK_OFFICER_CODE` environment variable, which is never written in the repository. The same goes for `DATABASE_URL`. The diseases page takes every line from the fact sheet it links and names no chemical; a test checks it.
- Do not add features beyond the proposal's FR-01 to FR-06 without a note in the scope table of the technical report.

## Before opening a pull request
```bash
python3 -m pytest --verbose
python3 scripts/measure_latency.py --runs 100
```
Both must run clean, and the latency line goes into the pull request description.
