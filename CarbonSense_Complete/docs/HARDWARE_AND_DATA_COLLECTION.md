# Hardware bring-up and data collection

## Existing components recorded from project discussion
ESP32 DevKit / ESP32-WROOM-32; INA219 I²C current sensor; SSD1306 128×64 I²C OLED; 5 V small fan; two small DC hobby motors; IRLZ44N MOSFET; axial flyback diode believed to be 1N4007; breadboard; jumper wires; LED and resistors. Verify markings and values physically before wiring.

## Sensor/display I²C wiring
- ESP32 3V3 -> INA219 VCC and OLED VCC (only if the modules support 3.3 V)
- ESP32 GND -> INA219 GND and OLED GND
- GPIO21 -> both SDA
- GPIO22 -> both SCL
Do not infer pin position from wire colour; read the printed labels.

## INA219 load path
For high-side sensing, supply positive -> VIN+; VIN- -> load positive; load negative -> driver/load return -> supply ground. Ensure common ground with ESP32 when using a separate isolated low-voltage DC supply. Never connect mains AC. Never connect motor terminals directly to an ESP32 GPIO.

## Motor cautions
Use a suitable low-side driver and confirm gate drive/current ratings. IRLZ44N may not fully enhance at 3.3 V gate drive. Flyback diode goes in parallel with a brushed DC motor for simple on/off control: cathode/striped end to motor positive; anode/unstriped end to motor negative/MOSFET drain. A 1N4007 is not appropriate for every high-frequency PWM application. Do not energize a motor circuit until current path, power supply, driver, and resistor values are checked.

## Collection protocol
For every condition:
1. Inspect and photograph wiring; record sensor and supply.
2. Start a unique `run_id` for each independent run.
3. Record a no-load/sensor baseline.
4. Measure each load separately; never switch multiple loads without recording the condition.
5. Include condition labels (e.g. fan low/high if controllable, motor no-load/loaded only with safe mechanical setup).
6. Collect at least 3–5 independent runs per class/condition; each run should contain many time samples.
7. Record raw data first; don't overwrite it with cleaned data.
8. Compare INA219 measurements with a reference meter when available; note calibration and uncertainty.
9. Keep `data_origin=hardware` only for readings actually collected from the physical device.
10. Never copy synthetic scenario data into the real-measurement dataset.

## Current prototype issue
The user observed bus voltage values around 0.004–0.012 V and current around 0 mA. Treat this as a failed/unfinished measurement setup, not a valid load measurement. Check sensor detection and I²C wiring, then verify the INA219 VIN+/VIN− load path before connecting a load.
