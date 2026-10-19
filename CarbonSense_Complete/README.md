# CarbonSense — AI-Powered Energy Forensics & Reduction Verification

CarbonSense is an open-source student IoT + machine-learning project that connects electrical energy monitoring with load identification, anomaly detection, energy-waste investigation, recommendations, and Action–Measure–Verify analysis.

The system combines an ESP32/INA219 sensing node, a FastAPI ingestion service, SQLite storage, a dynamic browser dashboard, experiment datasets, and machine-learning workflows.

## Project Status

The ESP32 firmware has been uploaded successfully. Earlier serial output showed near-zero bus voltage and current, so physical measurement validation remains in progress.

The bundled datasets contain populated, plausible **simulated development profiles** that support software development, testing, and initial ML evaluation. They are not represented as actual collected measurements.

The project includes the principal software components for its intended workflow. Real-hardware accuracy, end-to-end reliability, and experimentally verified energy and carbon reductions must be established through controlled testing.

## Two-Stage Study

### 1. College Prototype

The prototype studies three low-voltage loads:

- LED circuit
- 5 V DC fan
- Small DC hobby motor

The ESP32 and INA219 collect electrical measurements under controlled operating conditions. These measurements can be used to develop load-classification models, establish baselines, investigate unusual consumption, and evaluate energy-saving interventions.

### 2. Larger-System Scenario

A separate illustrative dataset represents:

- Lighting circuits
- Ventilation fans
- Pump motors
- Office equipment

This stage exercises the software and analytical workflow with a broader set of load categories. Its data are simulated software scenarios, not measurements collected from an actual facility.

**Safety:** The larger-system scenario is for software development and analysis only. Do not connect the low-voltage prototype directly to mains electricity. Any future mains-energy monitoring requires appropriately rated, certified equipment and safe installation.

## Included Machine-Learning Capabilities

- **Supervised load identification:** Random Forest classification with a run-aware holdout split and per-class evaluation metrics.
- **Anomaly detection:** Isolation Forest outlier detection, trained using normal-labelled training rows where available.
- **Per-load baseline analysis:** Compares observations with established load profiles to identify unusual changes.
- **Carbon Forensics:** Produces analytical explanations and Carbon Story summaries for changes in consumption.
- **Explainable alerts:** Highlights readings that may require investigation; an anomaly is not automatically proof of energy waste.
- **Opportunity ranking:** Prioritizes potential energy-saving actions using available measurements and analytical criteria.
- **Action–Measure–Verify:** Compares before-and-after energy measurements and calculates energy and estimated CO₂e changes.
- **Pre-trained development models:** Included for immediate software demonstration.

The bundled models were trained on simulated development datasets. Their predictions and evaluation metrics are development results, not evidence of accuracy on real hardware or at a real facility.

After collecting actual experiments, retrain and evaluate the models using your measured data. Keep independent experimental runs separate for testing to reduce data leakage.

## Carbon Accounting: Energy and CO₂e Calculations

CarbonSense estimates electricity-related greenhouse-gas emissions from measured or calculated energy consumption. It does not directly measure CO₂ emissions.

### 1. Power and energy

Electrical power is expressed in watts (W), and energy is expressed in watt-hours (Wh) or kilowatt-hours (kWh).

For a series of power measurements, energy can be approximated by integrating power over elapsed time:

\[
E_{\mathrm{Wh}} \approx
\sum_i P_i(\mathrm{W})\frac{\Delta t_i(\mathrm{s})}{3600}
\]

The corresponding kilowatt-hour value is:

\[
E_{\mathrm{kWh}} = \frac{E_{\mathrm{Wh}}}{1000}
\]

For readings in milliwatts, convert to watts before applying the energy calculation:

\[
P_{\mathrm{W}} = \frac{P_{\mathrm{mW}}}{1000}
\]

These calculations depend on valid timestamps, correct units, reliable sensor measurements, and appropriate handling of missing readings and sampling gaps.

### 2. Estimated electricity-related emissions

CarbonSense uses the following relationship:

\[
\mathrm{CO_2e\ (kg)} =
E_{\mathrm{kWh}}\times
EF_{\mathrm{kg\ CO_2e/kWh}}
\]

Here, \(EF\) is the electricity emissions factor, expressed in kilograms of carbon-dioxide equivalent per kilowatt-hour.

The factor must be appropriate to the intended geographic region, reporting period, electricity system, and accounting methodology.

### 3. Default emissions factor

The current backend configuration uses:

`0.716 kg CO₂e/kWh`

This value is an **example default in the development implementation**. Its official source and suitability for the project's intended reporting context have not yet been established.

It must not be presented as a verified, current Indian grid emissions factor until its provenance has been checked.

Before using the factor for research findings or public carbon-savings claims:

1. Identify an authoritative emissions-factor source appropriate to the intended application, such as a relevant official Indian electricity-grid emissions publication.
2. Record the publication or dataset title, issuing organization, reporting year, geographic scope, factor value, units, and access link.
3. Confirm whether the factor represents the accounting approach intended for the project.
4. Update the configuration and documentation with the verified factor and its source.
5. Record the factor used for each reported result so that calculations can be reproduced.

The backend supports configuring the emissions factor through environment configuration. Consult `backend/README.md` and the backend implementation for the exact setting supported by the current version.

Until the source is verified, treat calculations using the default as **illustrative estimates**, not official carbon-accounting results.

### 4. Action–Measure–Verify calculations

For comparable measurements collected before and after an intervention:

\[
\Delta E_{\mathrm{kWh}} =
E_{\mathrm{before}}-E_{\mathrm{after}}
\]

When the baseline energy is greater than zero:

\[
\mathrm{Reduction\ (\%)} =
\frac{E_{\mathrm{before}}-E_{\mathrm{after}}}
{E_{\mathrm{before}}}\times100
\]

The estimated change in electricity-related emissions is:

\[
\Delta \mathrm{CO_2e} =
\Delta E_{\mathrm{kWh}}\times EF
\]

A positive value represents an estimated reduction when the post-intervention energy is lower than the baseline energy. A negative value indicates an estimated increase.

For a fair comparison, measurements should cover equivalent durations and comparable operating conditions. The calculation must also account for sensor limitations and missing data. A calculated difference is not sufficient by itself to establish causation or prove that an intervention will produce the same reduction in other settings.

### 5. Measurement, estimates, and verified results

CarbonSense distinguishes among:

- **Measured values:** Voltage, current, and power reported by the connected sensing system.
- **Calculated values:** Energy derived from power measurements and elapsed time.
- **Estimated emissions:** CO₂e calculated using an explicitly documented emissions factor.
- **Verified intervention results:** Before-and-after comparisons supported by valid, comparable experimental measurements.

The project does not claim direct measurement of CO₂ emissions. Anomaly detection identifies patterns for investigation, while energy and carbon reductions require separate evidence from controlled comparisons.

## Software Architecture

The intended workflow is:

**Sense → Investigate → Identify → Decide → Act → Verify**

1. The ESP32 reads electrical measurements from the INA219.
2. The firmware displays local readings and sends data to the backend over Wi-Fi.
3. FastAPI validates and stores incoming readings in SQLite.
4. The analytics and ML components classify known loads, flag unusual observations, compare measurements against baselines, and rank potential actions.
5. The dashboard displays readings, trends, alerts, and analytical results.
6. The user performs a controlled intervention.
7. CarbonSense compares the before-and-after measurements and calculates the corresponding energy change and estimated CO₂e change.

The validity of the final result depends on the quality of the measurements, the experimental design, the ML evaluation, and the documented emissions factor.

## Run on macOS

Extract the project ZIP and open three Terminal tabs from the extracted `CarbonSense_Complete` directory.

### 1. Start the backend and API

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000/docs` to inspect and test the API.

### 2. Start the dashboard

In a second Terminal tab:

```bash
cd dashboard
python3 -m http.server 5173
```

Open `http://127.0.0.1:5173`.

The dashboard uses `http://127.0.0.1:8000` by default. It remains empty until readings are stored. You can submit a test reading through the API documentation or connect the ESP32.

### 3. Retrain the ML pipelines

The development models are already bundled. To retrain the prototype model:

```bash
cd ml
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python train_evaluate.py \
  --data ../data/college_prototype/synthetic_readings.csv \
  --out models/college_prototype
```

To retrain the larger-system scenario model:

```bash
python train_evaluate.py \
  --data ../data/real_world_scenario/synthetic_readings.csv \
  --out models/larger_system_scenario
```

The default API model path is `ml/models/college_prototype`. To switch to the larger-system model, set `CARBONSENSE_MODEL_DIR` to the absolute path of `ml/models/larger_system_scenario` before starting the backend, then restart the backend.

The bundled evaluation results are based on simulated development data. Retraining on the same synthetic data does not establish real-world model performance.

## Data Integrity

- Synthetic dataset rows are identified by `data_origin=simulated_development`.
- The live dashboard does not automatically insert simulated readings.
- ESP32 uploads are marked `hardware` by the firmware.
- Keep actual hardware measurements separate from synthetic datasets when reporting experimental results.
- Preserve raw experimental observations and document preprocessing, exclusions, and measurement conditions.
- Do not report synthetic values as measured results or present development-model accuracy as real-hardware accuracy.
- Store credentials locally and do not commit Wi-Fi passwords, API secrets, or other private configuration to GitHub.

## Validation Checklist

Before reporting the system as experimentally validated, verify the following:

- [ ] INA219 voltage, current, and power measurements are stable and plausible for each test load.
- [ ] OLED readings agree with the sensor values sent to the backend.
- [ ] Readings are timestamped, stored correctly, and available through the API and dashboard.
- [ ] Missing, invalid, or interrupted measurements are handled appropriately.
- [ ] ML models are retrained and evaluated using actual experimental data.
- [ ] Independent experiment runs are held out for evaluation.
- [ ] Per-class precision, recall, confusion matrices, and other appropriate metrics are recorded.
- [ ] Anomaly alerts are examined against known normal and abnormal test conditions.
- [ ] Energy calculations are checked against known test cases and consistent units.
- [ ] The emissions factor's source, scope, reporting period, and units are documented.
- [ ] Before-and-after energy comparisons use comparable durations and operating conditions.
- [ ] Carbon estimates are clearly distinguished from directly measured values and experimentally verified energy reductions.

## Limitations and Future Work

CarbonSense is an educational research prototype focused on low-voltage DC loads. Its current hardware is not a mains-energy meter, and its development datasets do not establish performance at a real facility.

Future work includes collecting a larger real-hardware dataset, validating the ML models on independent experiments, improving sensor calibration and fault handling, documenting an authoritative emissions factor, strengthening deployment security, and evaluating longer-duration interventions.

The long-term goal is to provide a transparent, affordable energy-intelligence system that connects electrical measurements with explainable investigation and experimentally supported energy-reduction opportunities.
