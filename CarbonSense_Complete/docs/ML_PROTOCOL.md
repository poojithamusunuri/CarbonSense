# ML training and evaluation protocol

## Separate models by study stage
- Prototype classifier: labels `led`, `fan`, `dc_motor` from low-voltage prototype features.
- Larger-system scenario classifier: labels `lighting_circuit`, `ventilation_fan`, `pump_motor`, `office_equipment`.

Train separate models; do not mix these labels into one classifier unless a future experiment explicitly defines a shared taxonomy. Unknown/out-of-distribution detection is a separate task and must be validated on genuinely unseen loads, not inferred from a closed-set classifier alone.

## Features and split
Features: voltage_v, current_ma, power_mw, energy_wh, temperature_c, duty_cycle_pct. Split by `run_id` where possible to reduce leakage. Report per-class precision/recall/F1, confusion matrix, test run counts and source type.

## Synthetic data limitation
Current bundled profiles are simulated development data. Scores from them verify that the code runs; they do not establish real hardware accuracy. Final claims require independently collected, calibrated hardware runs and held-out operating conditions.

## Energy/carbon logic
Power is V × I with consistent units. Integrate power over time to get energy. CO₂e estimate = energy_kWh × documented emissions factor (kg CO₂e/kWh). Record the factor's source, region, year and version. A classifier prediction alone cannot verify carbon reduction; comparable measured before/after periods are required.


## Model artifacts and API integration
The repository includes `ml/models/college_prototype/` and `ml/models/larger_system_scenario/` containing a classifier, Isolation Forest detector, and evaluation JSON. The API defaults to the college prototype model. To use the scenario model, set `CARBONSENSE_MODEL_DIR` to the absolute path of `ml/models/larger_system_scenario` before starting the backend. These bundled models were trained on simulated development data and exist to make the software pipeline demonstrable; replace/retrain them with calibrated hardware data before making research claims.

## Run the models
From the `ml/` directory, install `pip install -r requirements.txt`, then run:

```bash
python train_evaluate.py --data ../data/college_prototype/synthetic_readings.csv --out models/college_prototype
python train_evaluate.py --data ../data/real_world_scenario/synthetic_readings.csv --out models/larger_system_scenario
```

Each output directory contains `load_classifier.joblib`, `anomaly_detector.joblib`, and `evaluation.json`. The API defaults to the college prototype artifacts. The dashboard can request a classifier prediction for the latest API reading and displays Isolation Forest flags when the model is available.
