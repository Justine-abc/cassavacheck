CassaCheck - Technical Report

Calibrated and abstaining cassava leaf disease diagnosis, with district information shown beside the result.

Repository: https://github.com/Justine-abc/cassavacheck 
Walkthrough video (technical): https://youtu.be/vphYf2nHZVs?si=BnazzsQD0cSPHhoS
Technical report: https://docs.google.com/document/d/1vgKi-RFGxIOhqZMwrSjIWANC7bGGATMXlVcnxsnRL3s/edit?usp=sharing

Project overview

A farmer or extension officer uploads one photograph of a cassava leaf. The system returns one of five conditions (cassava bacterial blight, brown streak disease, green mite damage, mosaic disease, healthy) with a calibrated confidence, or says "not sure" and asks three follow-up questions when the confidence is below a threshold fixed on validation data. Published district survey information is shown in a separate panel and never changes the diagnosis. Advice is management-level and never names a pesticide.

Research protocol behind it: public Makerere field photographs (21,397) with a published 70/15/15 split and near-duplicate control; MobileNetV3-Large fine-tuned with class-weighted loss; temperature scaling and an abstention threshold fitted on one half of the validation split and measured on the other; the test split and the Ghanaian CCMT set are reserved for the final evaluation.

Current results (validation split, one seed, two epochs)
Measure	Value
Accuracy / macro-F1	0.8237 / 0.7109
Per-class F1	CBB 0.5955, CBSD 0.7123, CGM 0.6838, CMD 0.9292, healthy 0.6336
Temperature / threshold	0.931 / 0.6455 (target coverage 0.80)
ECE before / after calibration (held-out half)	0.0275 / 0.0296
Abstention (held-out half)	coverage 0.791; accuracy 0.907 on retained answers vs 0.825 on all; 0.513 on abstained
Forward pass, 1 CPU thread, batch 1, median of 100	19.8 ms (MobileNetV3-Large); 61.7 ms (ResNet-18 architecture)
End to end	261 ms (laptop Chrome); under 1 s (iPhone Safari over hotspot)
Technical requirements
Item	Version
Python	3.10 to 3.12 (PyTorch 2.3.1 has no wheel for 3.13 or newer)
PyTorch / torchvision	2.3.1 (CPU build) / 0.18.1
FastAPI / Uvicorn	0.111.0 / 0.30.1
scikit-learn, pandas, numpy, Pillow, imagehash	pinned in requirements.txt
pytest, httpx	8.3.2, 0.27.0 (tests)
Training	Google Colab, T4 GPU (notebooks 01, 02, 04)
Tested on	Ubuntu (Chrome, Firefox), iPhone 14 Pro Safari; laptop: HP ProBook 430 G8, Intel Core i7-1165G7, 8 GB RAM, Ubuntu 26.04
Installation
bash
git clone https://github.com/Justine-abc/cassavacheck.git
cd cassavacheck
uv venv --python 3.12 .venv            # or: python3.12 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
uv pip install torch==2.3.1 torchvision==0.18.1 --index-url https://download.pytorch.org/whl/cpu   # or pip
uv pip install --requirement requirements.txt

The model weights (models/mobilenetv3_baseline.pt, 16.3 MB) and the calibration values (models/calibration.json) are in the repository; no download is needed to run the product.

Run
bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
Web interface: http://localhost:8000/
Swagger UI: http://localhost:8000/docs
Health, with the active calibration values: http://localhost:8000/health
From a phone on the same network: http://<laptop IP>:8000/ (choose "Files" in the picker; direct camera capture needs HTTPS)
Test and measure
bash
python3 -m pytest --verbose                      # 16 unit and integration tests
python3 -m scripts.measure_latency --runs 100    # forward-pass latency, one CPU thread
Repository structure
api/
  main.py          routes only: /health, /districts, /log, /diagnose, /
  classifier.py    abstract ImageClassifier; MobileNetV3Classifier, ResNet18Classifier
  calibration.py   Calibrator (temperature scaling), AbstentionGate, Decision, CalibrationSettings
  districts.py     DistrictRepository, DistrictPrevalence (CSV-backed, season fallback)
  advice.py        AdvisoryService; advice and follow-up questions as data; forbidden-word guard
  log_store.py     DiagnosisLog (SQLite; anonymised)
  config.py        paths and class names
  static/index.html  one-page interface: confident state, not-sure state with questions, district panel
tests/             test_calibration.py, test_districts_and_advice.py, test_api.py
scripts/           measure_latency.py
notebooks/         01_data_and_split, 02_baseline_train, 04_calibration_abstention
data/              split_v1_seed42.csv (published split), district_prevalence.csv
models/            mobilenetv3_baseline.pt, calibration.json
docs/              technical report, design exports (docs/design), screenshots, deployment plan, video script
CONTRIBUTING.md    design constraints every change must respect
Scope status against the approved proposal

Completed: FR-01 to FR-06, near-duplicate split, calibration and abstention, latency measurement, tests. Partial: district table (2 of 13 districts verified), baseline (one seed, two epochs; ResNet-18 implemented, not trained), interface (designed in six screens, implemented as one static page). Scheduled: five-seed runs (2 November), external evaluation on CCMT (9 November), Render deployment, React build. Details and evidence in the technical report, Section 1.

Deployment plan

See docs/deployment_plan.md: FastAPI and the page on Render (HTTPS), PostgreSQL for the district table and the log, calibration values loaded with the weights.










# CassaCheck: initial software product

**Repository:** https://github.com/Justine-abc/cassavacheck

## Description
CassaCheck classifies a field photograph of a cassava leaf into one of five conditions: cassava bacterial blight (CBB), cassava brown streak disease (CBSD), cassava green mite (CGM), cassava mosaic disease (CMD) or healthy, and returns the class with its confidence. Published district-level disease information is shown beside the result and is never combined with it. This initial product contains the data pipeline with a published split, a first MobileNetV3-Large baseline with its metrics, a web interface, a Swagger API interface and a command-line checker.

## 1. Requirements and tools
| Requirement (from the proposal) | How this product meets it | Tool |
|---|---|---|
| Accept a leaf photo from a browser and return five class probabilities | `POST /diagnose` in `api/main.py`; upload page at `/` | FastAPI, PyTorch |
| Show district and season information separately from the diagnosis | `GET /districts` and the panel on the web page, fed by `data/district_prevalence.csv` | FastAPI |
| Published split with near-duplicate control | `data/split_v1_seed42.csv` from `notebooks/01_data_and_split.ipynb` | imagehash, scikit-learn |
| Lightweight model for CPU inference | MobileNetV3-Large fine-tuned from ImageNet weights | torchvision |
| Calibration and abstention | Planned next; temperature and threshold will be fitted on the validation split only | |

Why these tools: PyTorch and torchvision give pre-trained MobileNetV3 and a two-line head replacement; imagehash gives a perceptual fingerprint so near-identical photos stay in one split; scikit-learn gives the stratified group split and the metrics; FastAPI gives the API with Swagger UI generated at `/docs`; Google Colab gives a free T4 GPU for training.

## 2. Development environment setup
```bash
git clone https://github.com/Justine-abc/cassavacheck.git
cd cassavacheck
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install --requirement requirements.txt
```
Data: accept the competition rules at https://www.kaggle.com/competitions/cassava-leaf-disease-classification, create an API token on the Kaggle settings page, and paste it into the first cell of notebook 01. Python 3.10 to 3.12 is required (PyTorch 2.3.1 has no wheel for 3.13 or newer); on a newer system create the environment with `uv venv --python 3.12 .venv`. Install PyTorch as the CPU build first to avoid the 2 GB GPU download: `pip install torch==2.3.1 torchvision==0.18.1 --index-url https://download.pytorch.org/whl/cpu`, then `pip install --requirement requirements.txt`. The notebooks are written for Google Colab (Runtime, Change runtime type, T4 GPU); notebook 01 downloads the data (5.76 GB).

## 3. Run the product
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
- Web interface: http://localhost:8000/ (choose district and season, upload a photo, read the result card and the district panel)
- API interface (Swagger UI): http://localhost:8000/docs
- Command line, one image: `python3 demo.py path/to/leaf.jpg`

## 4. Data (notebook 01)
- 21,397 labelled field photographs, all 800 by 600 pixels. Class counts: CMD 13,158 (61.5%), healthy 2,577, CGM 2,386, CBSD 2,189, CBB 1,087.
- Near-duplicate check: perceptual hash (8 by 8) over all images found no two images sharing a fingerprint, so no grouping was needed; the check stays in the pipeline for the external dataset.
- Split, stratified by class, seed 42: train 14,977 / validation 3,210 / test 3,210, every class present in every split. Published as `data/split_v1_seed42.csv`.

## 5. Model (notebook 02)
MobileNetV3-Large, ImageNet pre-trained, classifier head replaced by a 5-way linear layer; hard-swish activations and squeeze-and-excitation blocks (see the layer summary in the notebook). Loss: class-weighted cross-entropy (CMD is 61% of labels). Optimiser: AdamW, learning rate 3e-4, cosine decay. Input 224 by 224, horizontal and vertical flips. Two epochs on a T4, about eight minutes; 4.2 million parameters.

## 6. Initial performance (validation split, 3,210 images, seed 42, 2 epochs)
| Metric | Value |
|---|---|
| Accuracy | 0.8237 |
| Macro-F1 | 0.7109 |
| Per-class F1 | CBB 0.5955, CBSD 0.7123, CGM 0.6838, CMD 0.9292, healthy 0.6336 |

Precision and recall per class are in the notebook output. The confusion matrix is in `docs/screenshots/confusion_matrix.png`; the largest remaining confusions are CMD photographs read as CGM (108 of 1,972) and healthy leaves read as CBB (52 of 387), which is what calibration and abstention are meant to catch in the next version. The test split is not read in this product; it is reserved for the final evaluation after calibration and abstention are frozen.

## 7. Designs
Screenshots in `docs/screenshots/`: the web page before upload, the result card with the district panel, the Swagger UI, and the `/diagnose` response. The page has one flow: choose district and season, upload a photo, read the result.

## 8. Deployment plan
See `docs/deployment_plan.md`: FastAPI and the static page on Render, PostgreSQL for the district table and the anonymised log, calibration and abstention loaded with the weights, latency measured as the forward pass at batch size 1 on one CPU core.

## 9. Video demo
Video: https://youtu.be/mjl7zWxg7eI?si=HbVunf069Q01zJS2

## Repository layout
```
api/main.py                 FastAPI: /health, /districts, /diagnose, Swagger at /docs, page at /
api/static/index.html       one-page web interface
data/district_prevalence.csv
data/split_v1_seed42.csv
demo.py                     command-line check for one image
docs/deployment_plan.md, docs/video_script.md, docs/screenshots/
models/mobilenetv3_baseline.pt   (16.3 MB, in the repository)
notebooks/01_data_and_split.ipynb, notebooks/02_baseline_train.ipynb
requirements.txt
```
