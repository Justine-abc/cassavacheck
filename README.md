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
Data: accept the competition rules at https://www.kaggle.com/competitions/cassava-leaf-disease-classification, create an API token on the Kaggle settings page, and paste it into the first cell of notebook 01. The notebooks are written for Google Colab (Runtime, Change runtime type, T4 GPU); notebook 01 downloads the data (5.76 GB).

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
| Accuracy | 0.8274 |
| Macro-F1 | 0.7102 |
| Per-class F1 | CBB 0.5707, CBSD 0.7110, CGM 0.6978, CMD 0.9356, healthy 0.6360 |

Precision and recall per class are in the notebook output. The confusion matrix is in `docs/screenshots/confusion_matrix.png`; the largest remaining confusions are CMD photographs read as CGM (89 of 1,972) and healthy leaves read as CBB (54 of 387), which is what calibration and abstention are meant to catch in the next version. The test split is not read in this product; it is reserved for the final evaluation after calibration and abstention are frozen.

## 7. Designs
Screenshots in `docs/screenshots/`: the web page before upload, the result card with the district panel, the Swagger UI, and the `/diagnose` response. The page has one flow: choose district and season, upload a photo, read the result.

## 8. Deployment plan
See `docs/deployment_plan.md`: FastAPI and the static page on Render, PostgreSQL for the district table and the anonymised log, calibration and abstention loaded with the weights, latency measured as the forward pass at batch size 1 on one CPU core.

## 9. Video demo
Video: VIDEO_LINK

## Repository layout
```
api/main.py                 FastAPI: /health, /districts, /diagnose, Swagger at /docs, page at /
api/static/index.html       one-page web interface
data/district_prevalence.csv
data/split_v1_seed42.csv
demo.py                     command-line check for one image
docs/deployment_plan.md, docs/video_script.md, docs/screenshots/
models/mobilenetv3_baseline.pt   (download link below if not in the repository)
notebooks/01_data_and_split.ipynb, notebooks/02_baseline_train.ipynb
requirements.txt
```
