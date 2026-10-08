# Deployment plan

## Now (initial product)
- Model trained in Google Colab (free T4); weights saved as `models/mobilenetv3_baseline.pt`.
- API: FastAPI served locally with `uvicorn api.main:app --host 0.0.0.0 --port 8000`.
- Interfaces: Swagger UI at `/docs`; one-page web interface at `/`.

## Next (by the final demonstration)
- API and static page on Render (shared-CPU instance); model weights bundled with the service.
- PostgreSQL on Render for the district prevalence table, advisory rules and the anonymised log.
- Calibration temperature and abstention threshold fitted on the validation split, frozen, and loaded with the weights.
- Latency measured as the forward pass at batch size 1 on one CPU core (median of 100 runs), reported in the README.

## Not planned
- No accounts, no location reading from the phone, no pesticide recommendations.
