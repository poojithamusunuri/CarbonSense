# Stage 2: larger-system scenario and future field pilot

The larger-system scenario uses different categories than the college prototype: lighting circuit, ventilation fan, pump motor, and office equipment. It is populated with plausible simulated profiles to develop the software workflow and ML pipeline before a real site pilot.

## Not field measurements
No actual building/facility dataset was supplied. Do not present the scenario CSV as measurements collected from a real site. When a pilot is possible, replace it with properly authorized, calibrated, isolated measurements.

## Before a real pilot
- Define whether the boundary is a plug load, submeter, or facility circuit.
- Use certified, appropriately rated isolated equipment and qualified electrical personnel for AC/building measurements. The current ESP32/INA219 prototype is intended for low-voltage DC experiments only.
- Document calibration, sampling rate, accuracy, drift, clock synchronization, device identity, network loss, and maintenance.
- Preserve raw records and version transformations.
- Record the grid emissions factor source, region, year, and version before estimating CO₂e.
- Compare equivalent baseline/intervention windows and report uncertainty.
- Evaluate on held-out devices/sites; include unknown conditions and abstention.
