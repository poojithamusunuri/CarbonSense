# Data inventory

These bundled time series are realistic-looking **simulated development profiles**, not data collected from the user's hardware or a real site. They are supplied to make the dashboard and ML workflow runnable while hardware data collection is completed.

- `college_prototype/synthetic_readings.csv`: 2,520 rows across LED, 5 V fan, and DC motor; each has multiple operating conditions and independent run IDs.
- `real_world_scenario/synthetic_readings.csv`: 3,360 rows across illustrative site-pilot categories: lighting circuit, ventilation fan, pump motor, and office equipment; multiple operating conditions and independent run IDs.

The two datasets intentionally model different scales and load categories. Replace these profiles with measured data before presenting them as experimental results. Do not describe the larger-system scenario as field data.
