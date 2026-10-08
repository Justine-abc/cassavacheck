# Video demo script (target 6 to 8 minutes)

0:00 One sentence: what the product does (photo of a cassava leaf in, one of five conditions out, with confidence; district risk shown beside it). No research background.
0:30 Repository tour: README, notebooks, api, data. Show requirements.txt and the setup commands.
1:30 Notebook 01: class distribution chart, sample grid, image-size distribution, duplicate count, split counts table.
3:00 Notebook 02: model summary (layers, activations, parameters), training loop, the metrics cell: accuracy, precision, recall, F1 per class, confusion matrix.
5:00 Start the API: `uvicorn api.main:app --reload`. Open /docs (Swagger): call /health, then /diagnose with a test image; show the JSON.
6:30 Open the web page at /: choose district and season, upload a leaf photo, show the result card and the district panel; upload a second photo.
7:30 Deployment plan in one breath (Render, Postgres, calibration and abstention next). End.
