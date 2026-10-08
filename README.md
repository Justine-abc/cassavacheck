# CassaCheck: initial software product

**Repository:** https://github.com/Justine-abc/cassacheck

## Description
CassaCheck classifies a photograph of a cassava leaf into one of five conditions (cassava bacterial blight, cassava brown streak disease, cassava green mite, cassava mosaic disease, healthy) and returns the class with its confidence. Published district-level disease information is shown beside the result, never combined with it. This initial product contains the data pipeline with a published split, a first MobileNetV3-Large baseline with its metrics, and two interfaces: Swagger UI and a one-page web interface.

## Requirements this product addresses
| Requirement (from the proposal) | How it is met here |
|---|---|
| FR-01 Accept a leaf photo from a browser | `/diagnose` endpoint and the upload page at `/` |
| FR-02 District and season chosen from lists; published incidence shown separately | `/districts` endpoint and the panel on the web page, fed by `data/district_prevalence.csv` |
| FR-03 Five-class probabilities from the classifier | MobileNetV3-Large baseline, `models/mobilenetv3_baseline.pt` |
| Split published; duplicates kept together | `data/split_v1_seed42.csv` produced by `notebooks/01_data_and_split.ipynb` |
| Calibration and abstention (FR-04, NFR) | Planned next; threshold and temperature will be fitted on the validation split only |

## Tools and why
| Tool | Why |
|---|---|
| Python 3.11, PyTorch, torchvision | Pre-trained MobileNetV3-Large, fine-tuning, export |
| imagehash | Perceptual hash to keep near-duplicate photos in one split |
| scikit-learn | Stratified group split, precision, recall, F1, confusion matrix |
| torchinfo | Layer-by-layer model summary |
| FastAPI + Uvicorn | REST API with automatic Swagger UI at `/docs` |
| Google Colab (T4) | Free GPU for training |

## Set up the environment
```bash
git clone https://github.com/<your-username>/cassacheck.git
cd cassacheck
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install --requirement requirements.txt
```
Data: accept the competition rules at https://www.kaggle.com/competitions/cassava-leaf-disease-classification, create an API token (Kaggle, Settings, API), and place `kaggle.json` next to the notebooks. Notebook 01 downloads the data (about 6 GB; run it in Colab).

## Run
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
Then open http://localhost:8000/ (web page) or http://localhost:8000/docs (Swagger UI).

## Notebooks
- `notebooks/01_data_and_split.ipynb`: download, class counts and distribution chart, sample grid, image-size distribution, near-duplicate detection, stratified group split, split file.
- `notebooks/02_baseline_train.ipynb`: model architecture summary, training, metrics (accuracy, precision, recall, F1 per class, confusion matrix), weights export.

## Initial performance (validation split, <N> epochs, seed 42)
| Metric | Value |
|---|---|
| Accuracy | <fill> |
| Macro-F1 | <fill> |
| Per-class F1 | CBB <fill>, CBSD <fill>, CGM <fill>, CMD <fill>, healthy <fill> |

## Designs
Screenshots of the web page and Swagger UI are in `docs/screenshots/`. The page has one flow: choose district and season, upload a photo, read the result card and the district panel.

## Deployment plan
See `docs/deployment_plan.md`.

## Video demo
Link: <fill>
