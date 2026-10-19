# CarbonSense API

FastAPI + SQLite ingestion and analysis API. Run from the repository root with `uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000`, or from `backend/` with `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.

Important endpoints:
- `GET /api/v1/health` — service status
- `POST/GET /api/v1/readings` — store and query measurements
- `GET /api/v1/summary` — summary by load
- `GET /api/v1/analytics/forensics` — per-load baseline comparison and Carbon Story
- `GET /api/v1/analytics/opportunities` — transparent, measured-power opportunity ranking
- `GET /api/v1/analytics/carbon` — integrate hardware-tagged power readings and estimate CO₂e
- `GET /api/v1/ml/status` — model availability and evaluation metadata
- `POST /api/v1/ml/predict` — classify the latest measurement signature
- `GET /api/v1/ml/anomalies` — Isolation Forest anomaly flags when model is available
- `POST/GET /api/v1/interventions` — Action–Measure–Verify records
- `GET /api/v1/export.csv` — export readings

Configure the grid factor with `CARBONSENSE_GRID_FACTOR_KG_PER_KWH` and its provenance with `CARBONSENSE_GRID_FACTOR_NOTE`. The default factor is an example only and must be checked against a current official source for the relevant region/year before reporting. Configure `CARBONSENSE_MODEL_DIR` to switch from `ml/models/college_prototype` to `ml/models/larger_system_scenario`.

Models bundled with the project are trained on simulated development data and are intended to make the code demonstrable. Retrain and evaluate using actual measured runs before making accuracy claims.
