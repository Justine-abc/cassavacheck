# CassaCheck

Cassava leaf disease diagnosis for Rwanda that reports a calibrated confidence and says "not sure" instead of guessing.

| | |
|---|---|
| Live app | https://cassacheck.onrender.com (free plan: the first visit after a quiet period takes up to a minute) |
| Repository | https://github.com/Justine-abc/cassavacheck |
| Technical report | https://docs.google.com/document/d/1vgKi-RFGxIOhqZMwrSjIWANC7bGGATMXlVcnxsnRL3s/edit?usp=sharing (PDF copy in `docs/`) |
| Walkthrough video (technical report) | https://youtu.be/vphYf2nHZVs?si=BnazzsQD0cSPHhoS |
| Earlier submissions | See [Earlier submissions](#earlier-submissions) at the end |

## What it does

A farmer or extension officer uploads one photograph of a cassava leaf. CassaCheck returns one of five conditions (cassava bacterial blight CBB, brown streak disease CBSD, green mite CGM, mosaic disease CMD, healthy) with a calibrated confidence. When the confidence is below a threshold fixed on validation data, it does not name a condition: it says "not sure", asks four questions about the field and lets the farmer send the case to the farmer promoter or sector agronomist.

- A photo with too little leaf colour (a screenshot, a wall) is refused before the model sees it.
- Advice is management steps only. It never names a pesticide or a dose, and a test enforces this.
- Published district survey information (CBSD incidence in the 13 surveyed districts, 2019) is shown beside the result and never changes the diagnosis.
- Farmers need no account, and no photos or names are stored. The officer's list keeps district, season, result and answers, and only an extension officer with the access code can open it. A phone number is stored only if the farmer ticks consent when sending a case, and it is deleted when the officer answers the case or after 30 days.

## The web app

| Page | Address | Purpose |
|---|---|---|
| Diagnose | `/` | District and season, photo by camera, file or drag and drop, three sample field photos |
| Result | `/result` | Diagnosis or "not sure", confidence against the decision line, advice, questions, referral |
| How it works | `/how-it-works` | What the model is, what the confidence means, why it says "not sure" |
| Diseases | `/diseases` | Cause, symptoms, spread and prevention without chemicals for the four diseases, with sources and an example photo |
| My case | `/my-case` | The farmer types the case number and check code to see the case status and the officer's answer |
| Officer view | `/officer` | Recent cases and referrals by district; the officer sets the case status and writes a note to the farmer. Needs the officer access code. Reached from the "Officer sign-in" link in the header, not from the farmer's menu |

Every farmer page can be switched between English and Kinyarwanda (EN / RW in the header). The officer view is in English.

The API is documented at `/docs` (Swagger UI) and `/health` shows the loaded model, temperature, threshold and leaf check cut-off. The sample photos are my own, taken in Busanza, Kanombe sector, Kicukiro district on 31 October 2026. They carry no disease label.

## Added after the report was submitted (November 2026)

The technical report describes the system at commit `d32ad17`. These additions came after it. None of them changes the model, the temperature, the threshold or any reported number.

- **Referral loop.** A referred case gets a case number and a six-character check code. The officer sets its status (received, seen, visit planned, answered) and writes a note, and the farmer reads both on the My case page. The note follows the same rule as the advice: no chemical, no dose.
- **Consent before contact.** The farmer can tick "the officer may call me" and give a Rwandan mobile number, so the officer can arrange the visit and find the field. Without consent no number is asked for. The number is never shown to the farmer page, never exported in the CSV, and is deleted when the case is answered or after 30 days.
- **Persistent case log.** PostgreSQL when `DATABASE_URL` is set; SQLite otherwise.
- **Kinyarwanda.** All farmer pages, advice and follow-up questions. Disease names keep the English code beside them.
- **Interface.** The farmer's menu is a bar at the bottom on a phone, within reach of the thumb, and moves into the header on a wide screen. Officers reach their page from a small "Officer sign-in" link in the header. The home page opens with one of my own field photos. The Diseases page and a confident result show a labelled example photo beside the farmer's leaf, for CBB, CGM and CMD. These examples are three CCMT photos (Mensah et al., 2023, CC BY 4.0), credited on screen and used for display only; CCMT has no brown streak class, so CBSD has none. While the server works, the steps it performs are listed one after another.

Still future work: individual officer accounts limited to a district (one shared access code today), SMS or USSD updates for phones without internet, a free helpline, and a usability study with farmers and extension officers.

## Method

- Data: Makerere cassava leaf dataset (Kaggle competition), 21,397 field photographs. Published split, stratified by class, seed 42: train 14,977 / validation 3,210 / test 3,210 (`data/split_v1_seed42.csv`). Near-duplicate check by perceptual hash.
- Model: MobileNetV3-Large fine-tuned from ImageNet weights with class-weighted cross-entropy (CMD is 61.5% of labels). Five seeds of MobileNetV3-Large and ResNet-18 trained for 8 epochs; the deployed model is MobileNetV3-Large seed 1, chosen on validation macro-F1.
- Calibration and abstention: temperature scaling and the abstention threshold are fitted on one half of the validation split, measured on the other half, then frozen in `models/calibration.json`. They are never refitted on the test set or in the API.
- Evaluation: the internal test split and the external CCMT set from Ghana are evaluated only after everything is frozen and are never used for any choice. Notebook 04b was run twice (CPU, then GPU) with identical code and frozen values; the results agree to the fourth decimal. CCMT is never used for tuning.

## Results

Deployed model: MobileNetV3-Large, 8 epochs, seed 1 (notebooks 03, 04b and 05).

| Measure | Value |
|---|---|
| Validation macro-F1 (model selection) | 0.7439 |
| Temperature / threshold | 1.1514 / 0.6752 (target coverage 0.80, fitted on the validation fit half) |
| ECE before / after calibration, 15 bins (validation measure half) | 0.0249 / 0.0160 |
| Internal test, 3,210 images: accuracy / macro-F1 | 0.8346 / 0.7246 (macro-F1 bootstrap 95% interval 0.705 to 0.745) |
| Per-class F1 (internal test) | CBB 0.5436, CBSD 0.7290, CGM 0.7597, CMD 0.9346, healthy 0.6559 |
| ECE before / after calibration, 15 bins (internal test) | 0.0294 / 0.0116 |
| Abstention (internal test) | coverage 0.792; accuracy 0.916 on answered photos vs 0.835 on all; 0.523 on abstained |
| External test, CCMT Ghana, 6,027 images: accuracy / macro-F1 over the 4 shared classes | 0.6187 / 0.6659 |
| ECE before / after calibration, 15 bins (CCMT) | 0.1595 / 0.1269 |
| Abstention (CCMT) | coverage 0.6441; accuracy 0.7439 on answered photos; 0.3921 on abstained |
| Leaf check (notebook 06) | cut-off 0.1764 plant-colour fraction, 1st percentile of the validation fit half; 8 of 1,605 real leaves refused on the other half |
| Forward pass, 1 CPU thread, batch 1, median of 100 | 19.8 ms (MobileNetV3-Large); 61.7 ms (ResNet-18 architecture) |
| End to end | 261 ms (laptop Chrome); under 1 s (iPhone Safari over hotspot) |

Macro-F1 averages the per-class F1 scores with equal weight, so the rare classes count as much as CMD. Plain accuracy is reported for reference only because of the class imbalance.

## Run it locally

Python 3.10 to 3.12 is required (PyTorch 2.3.1 has no wheel for 3.13 or newer).

```bash
git clone https://github.com/Justine-abc/cassavacheck.git
cd cassavacheck
uv venv --python 3.12 .venv            # or: python3.12 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
uv pip install torch==2.3.1 torchvision==0.18.1 --index-url https://download.pytorch.org/whl/cpu   # or pip
uv pip install --requirement requirements.txt
export CASSACHECK_OFFICER_CODE=choose-a-code   # Windows: set CASSACHECK_OFFICER_CODE=choose-a-code
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Open http://localhost:8000/. The officer view is at http://localhost:8000/officer and asks for the code you exported; without it the case log stays closed. From a phone on the same network: `http://<laptop IP>:8000/` (direct camera capture needs HTTPS, so choose a file there; the deployed app has HTTPS).

The model weights (`models/mobilenetv3_baseline.pt`, 16.3 MB), the calibration values and the leaf check cut-off are in the repository; no download is needed to run the app. The notebooks are written for Google Colab with a T4 GPU and download the data with a Kaggle API token stored as a Colab secret.

## Test and measure

```bash
python3 -m pytest --verbose                      # 29 unit and integration tests
python3 -m scripts.measure_latency --runs 100    # forward-pass latency, one CPU thread
```

## Deployment

One Render web service defined in `render.yaml` (free plan, Python 3.12, CPU-only PyTorch from `requirements-deploy.txt`). Every push to `main` redeploys it. The free plan sleeps when idle, so the first visit after a pause takes about a minute. Without a database the officer log is cleared on each restart; with `DATABASE_URL` set in the Render dashboard to a hosted PostgreSQL address, the log and the cases survive restarts. The address is a secret and is never written in the repository. Details in `docs/deployment_plan.md`.

## Repository structure

The system architecture diagram and the job of each component are in [docs/architecture.md](docs/architecture.md).

```
api/
  main.py          routes only
  classifier.py    MobileNetV3Classifier, ResNet18Classifier
  calibration.py   Calibrator (temperature scaling), AbstentionGate, Decision
  leaf_check.py    plant-colour check before the model
  districts.py     district survey table, never combined with the diagnosis
  advice.py        advice and follow-up questions as data; forbidden-word guard
  log_store.py     request log and referral cases; SQLite locally, PostgreSQL when DATABASE_URL is set
  referral.py      phone number and officer note checks
  static/          the six pages, shared app.js, i18n.js (English and Kinyarwanda), app.css, theme.js, sample photos
notebooks/         01 data and split, 02 baseline, 03 five seeds, 04 and 04b calibration
                   and internal test, 05 external test on CCMT, 06 leaf check
data/              split_v1_seed42.csv, district_prevalence.csv
models/            weights, calibration.json, leaf_check.json, diagrams
tests/             API, calibration, advice and districts, leaf check, referral cases, translations
scripts/           measure_latency.py, near_duplicates.py
docs/              architecture, technical report, design exports, screenshots, deployment plan
CONTRIBUTING.md    design constraints every change must respect
```

## Tools and versions

| Item | Version |
|---|---|
| Python | 3.10 to 3.12 |
| PyTorch / torchvision | 2.3.1 (CPU build) / 0.18.1 |
| FastAPI / Uvicorn | 0.111.0 / 0.30.1 |
| scikit-learn, pandas, numpy, Pillow, imagehash | pinned in `requirements.txt` |
| pytest, httpx | 8.3.2, 0.27.0 |
| Training | Google Colab, T4 GPU |
| Tested on | Ubuntu (Chrome, Firefox), iPhone 14 Pro Safari; HP ProBook 430 G8, Intel Core i7-1165G7, 8 GB RAM |

## Scope

Completed: FR-01 to FR-06, near-duplicate split, five seeds of both backbones, calibration and abstention with the internal test, external test on CCMT, leaf check, web app with five pages, latency measurement, tests. District table: all 13 districts of the 2019 national survey, CBSD incidence with its 95% interval and 300 plants examined per district (Nyirakanani et al., 2021, Table 1). System tests: `docs/testing/`. Matched-coverage comparison against a plain softmax classifier with its own validation threshold: notebook 07. Out of scope: field testing with farmers, any claim about yield.

## Licence

The code and the published split file are released under the MIT licence (`LICENSE`). The model weights in `models/` were trained on the Makerere cassava dataset, which Kaggle publishes subject to the competition rules, so the weights are shared for non-commercial research only. The training images are not included in this repository. CCMT (Mensah et al., 2023) is licensed CC BY 4.0. Library and font licences are listed in the final report, Table 3.7.

## Earlier submissions

Each link opens the repository exactly as it was on that date, so earlier work can be graded on the version that was submitted.

| Submission | Video | Code on that date |
|---|---|---|
| Initial software product | https://youtu.be/mjl7zWxg7eI?si=HbVunf069Q01zJS2 | https://github.com/Justine-abc/cassavacheck/tree/1a07a56 (18 Oct 2026) |
| Technical report | https://youtu.be/vphYf2nHZVs?si=BnazzsQD0cSPHhoS | https://github.com/Justine-abc/cassavacheck/tree/a5170f7 (26 Oct 2026) |
