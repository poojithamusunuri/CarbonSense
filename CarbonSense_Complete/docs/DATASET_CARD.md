# Dataset card

## Purpose
Provide populated, realistic-looking time-series profiles so the ingestion, dashboard, CSV export, and ML training/evaluation workflow can be developed before the physical prototype has been calibrated.

## Dataset A — College prototype
- Loads: `led`, `fan`, `dc_motor`
- Conditions: nominal/reduced supply/intermittent LED; nominal/reduced supply/restricted airflow fan; no-load/nominal/increased-load motor.
- Rows: 2,520; 24 independent condition/run groups.
- Origin: simulated development profiles, not measured hardware data.

## Dataset B — Larger-system scenario
- Loads: `lighting_circuit`, `ventilation_fan`, `pump_motor`, `office_equipment`
- Conditions: active/idle/reduced output/high demand variants.
- Rows: 3,360; 36 independent condition/run groups.
- Origin: simulated scenario profiles, not measured facility data.

## Limitations
The profiles are deliberately plausible, with noise and run variation, but do not model every sensor error, inrush event, power factor, calibration uncertainty, or site-specific behaviour. ML scores from these profiles must not be presented as real-world validation. Replace them with measured runs for final project claims.
