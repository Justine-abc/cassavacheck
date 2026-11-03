# Deployment

## What is deployed
- One web service on Render (free plan), defined in `render.yaml`. FastAPI serves the API and the five pages (diagnose, result, how it works, diseases, officer view) from `api/static/`.
- Python 3.12, CPU-only torch, packages in `requirements-deploy.txt` (training and notebook libraries stay in `requirements.txt`).
- Model weights and frozen values are bundled with the service: `models/mobilenetv3_baseline.pt` (MobileNetV3-Large, 8 epochs, seed 1), `models/calibration.json` (temperature and threshold, notebook 04b) and `models/leaf_check.json` (input check cut-off, notebook 06). Nothing is fitted on the server.
- Health check: `/health` reports the loaded weights, temperature, threshold and leaf check cut-off.

## Steps
1. Push the repository to GitHub.
2. On render.com: New, Blueprint, connect the GitHub repository. Render reads `render.yaml`, installs `requirements-deploy.txt` and starts `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.
3. Open `/health` on the new address and check that `weights_loaded` is true and the temperature is 1.1514.

## Known limits of the free plan
- The service sleeps after a period without visits; the first request after that takes about a minute while it starts.
- The officer log is a SQLite file on the service's disk. It is cleared when the service restarts or is redeployed, so it holds demonstration data only. A persistent database (PostgreSQL) is the step for real use.
- Memory: about 350 MB measured locally after six diagnoses with the same packages, under the plan's 512 MB.

## Not planned
- No accounts, no location reading from the phone, no pesticide recommendations.
