Markdown# CassaCheck: Initial Software Product

**Repository:** https://github.com/Justine-abc/cassavacheck

## Description
CassaCheck is a computer vision diagnostic tool that classifies field photographs of cassava leaves into five conditions: Cassava Bacterial Blight (CBB), Cassava Brown Streak Disease (CBSD), Cassava Green Mite (CGM), Cassava Mosaic Disease (CMD), and Healthy tissue. Designed specifically for agricultural edge deployment and low-resource settings, this initial software deliverable features a self-contained local CLI inference engine powered by a CPU-optimized MobileNetV3 architecture, complete data pipeline notebooks, baseline evaluation metrics, and verified visual demonstration logs.

---

## Software Demo & Rubric Alignment

### 1. Requirements & Tool Selection
- **Offline Edge Inference:** Optimized for agricultural extension workers and field conditions lacking reliable network or cloud infrastructure.
- **MobileNetV3 Architecture:** Selected for its minimal parameter count and rapid CPU inference capability without requiring heavy GPU acceleration.
- **PyTorch (CPU) & Pillow:** Lightweight runtime environment ensuring zero-overhead deployment without bloated web server dependencies.
- **Perceptual Hashing (`imagehash`) & Scikit-Learn:** Preserves dataset integrity by preventing near-duplicate leakage across train/validation splits.

### 2. Development Environment Setup
The repository is fully self-contained and reproducible on standard local environments:

```bash
# Clone the repository
git clone [https://github.com/Justine-abc/cassavacheck.git](https://github.com/Justine-abc/cassavacheck.git)
cd cassavacheck

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install torch torchvision --index-url [https://download.pytorch.org/whl/cpu](https://download.pytorch.org/whl/cpu)
pip install pillow
3. Navigation & Local Demo ExecutionRun local inference directly using the standalone CLI evaluation tool:Bashpython3 demo.py data/samples/cassava_sample_01.jpg
Verified Terminal Output:Plaintext=======================================================
           CASSACHECK LOCAL INFERENCE           
=======================================================
File Tested : data/samples/cassava_sample_01.jpg
Diagnosis   : healthy (61.94% confidence)
Overview    : Healthy Tissue - No significant disease symptoms identified.

Class Probabilities:
  - CBB     :   4.77%
  - CBSD    :  15.99%
  - CGM     :   3.93%
  - CMD     :  13.37%
  - healthy :  61.94%
=======================================================
Initial Performance (Validation Split, Seed 42)MetricBaseline ScoreValidation Accuracy68.4%Macro F1-Score0.61Per-Class F1 BreakdownCBB: 0.48, CBSD: 0.62, CGM: 0.58, CMD: 0.79, healthy: 0.62Notebooks & Pipeline Structurenotebooks/01_data_and_split.ipynb: Dataset acquisition, EDA, image resolution distributions, perceptual near-duplicate detection, and stratified split generation (data/split_v1_seed42.csv).notebooks/02_baseline_train.ipynb: Baseline model architecture summary, transfer learning training loop, multiclass evaluation metrics, and weights serialization (models/mobilenetv3_baseline.pt).Documentation & EvidenceDemonstration logs, execution screenshots, and architecture diagrams are located in docs/screenshots/ (including docs/screenshots/local_inference_demo.png). For additional architecture specifications, refer to docs/deployment_plan.md.
