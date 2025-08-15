# air-quality-monitoring-prague
# Air Quality Monitoring – Prague

## Overview
This project is a simple prototype for monitoring air quality in Prague using PM2.5, PM10, CO₂, temperature, and humidity sensors.

The repository contains:
- **air_quality_monitoring.py** – Python script (simulation mode by default)
- **Air_Quality_Monitoring_Framework.pdf** – Project framework/proposal

## How It Works
The Python script runs in two modes:
- **Simulation mode** – Generates fake but realistic sensor readings
- **Serial mode** – Reads from a connected Arduino/ESP32

## How to Run (Simulation Mode)
```bash
python3 air_quality_monitoring.py
## Future Improvements
- Integration with live sensors via Arduino/ESP32
- Cloud dashboard for real-time visualization
- Data analysis for pollution forecasting
