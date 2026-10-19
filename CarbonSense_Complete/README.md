# CarbonSense — AI-Powered Energy Forensics & Reduction Verification

A student IoT + ML project with an ESP32/INA219 sensing node, FastAPI ingestion service, dynamic browser dashboard, experiment datasets, and supervised load-classification workflow.

## Project status
The firmware has been uploaded to the ESP32. The serial output previously showed near-zero bus voltage and current, so physical measurement validation is still in progress. The bundled datasets are populated, plausible **simulated development profiles** to make software and ML development possible while the hardware is calibrated; they are not represented as actual collected measurements.

## Two-stage study
1. **College prototype:** LED, 5 V fan and DC motor under multiple operating conditions, using INA219 measurements.
2. **Larger-system scenario:** lighting circuit, ventilation fan, pump motor and office equipment profiles to exercise a site-scale workflow. These are illustrative software scenarios, not real facility measurements and not a safe instruction to connect this low-voltage prototype to mains.

## Included machine-learning capabilities
- Supervised Random Forest load identification with a run-aware holdout split and per-class evaluation.
- Isolation Forest outlier detection trained from normal-labelled training rows where available.
- Per-load baseline forensics, explainable alerts, Carbon Story summaries, and transparent opportunity ranking.
- Action–Measure–Verify calculations for measured power/energy changes and estimated CO₂e changes.
- Pre-trained development models are included for immediate demonstration. They were trained on simulated development datasets, so their predictions/metrics are not evidence of real hardware accuracy. Retrain after collecting actual experiments.

## Run on macOS
Open three Terminal tabs from the extracted `CarbonSense_Complete` folder.

**1. Backend + API**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Open `http://127.0.0.1:8000/docs` to inspect and test the API.

**2. Dashboard**
```bash
cd dashboard
python3 -m http.server 5173
```
Open `http://127.0.0.1:5173`. It uses the API at `http://127.0.0.1:8000` by default. It stays empty until readings are stored; use the API docs to send a test reading or connect the ESP32.

**3. Retrain both ML pipelines (optional; development models are already bundled)**
```bash
cd ml
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python train_evaluate.py --data ../data/college_prototype/synthetic_readings.csv --out models/college_prototype
python train_evaluate.py --data ../data/real_world_scenario/synthetic_readings.csv --out models/larger_system_scenario
```
The default API model path is `ml/models/college_prototype`. Set `CARBONSENSE_MODEL_DIR` to the absolute path of `ml/models/larger_system_scenario` before starting the backend to switch study stage. Restart the backend after changing model paths.

For a quick API test, open `/docs`, expand `POST /api/v1/readings`, and submit a sample with `device_id`, `load_label`, `voltage_v`, `current_ma`, and `power_mw`. Label test values as `test` in notes and do not report them as collected hardware data.

## Data integrity
Synthetic rows are clearly identified by `data_origin=simulated_development`. The live dashboard does not insert simulated rows automatically. Real ESP32 uploads are marked `hardware` by the firmware and stored in SQLite. Do not mix synthetic and real data when reporting measured results.
