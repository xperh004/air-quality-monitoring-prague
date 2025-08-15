"""
Project: Air Quality Sensor & Monitoring Framework (Arduino + Python)
Author: Helena Pereira de Barros 
Course: Sensors & Monitoring Systems (CZU, Prague)

---------------------------------------------------------------------
Our Mission: Build a simple, clear framework to monitor air quality in Prague.
Our Vision: A small prototype that can grow into a student-led city network of
low-cost sensors. The long-term goal is to inform schools, commuters, and
local authorities when pollution rises, and to support greener decisions.

This is a framework, not a full build. There is no physical Arduino here,
but the code is ready to read lines from an Arduino if connected later.

---------------------------------------------------------------------
WHAT THIS CODE DOES (FUNCTIONALITY)
---------------------------------------------------------------------
1) Opens a serial port (if available) to read air-quality values printed
   by an Arduino/ESP32. Expected line format:
     PM25:23.4;PM10:45.1;CO2:780;TEMP:21.9;HUM:47.3
2) If no device is available, it switches to SIMULATION mode and generates
   realistic random data so the script always runs.
3) Checks values against simple guideline thresholds and prints warnings.
4) Saves every reading to a CSV file (air_quality_log.csv) for later analysis.

---------------------------------------------------------------------
LIBRARIES USED (and why)
---------------------------------------------------------------------
- serial (pyserial): reads text lines from the USB/COM port (Arduino → PC).
- csv: writes logs to a CSV file so anyone can open it in Excel or R.
- time: timing between reads and small waits (e.g., after opening serial).
- random: creates fake data in SIMULATION mode (useful for demos).
- datetime: timestamps each reading for history and plots later.

---------------------------------------------------------------------
FUTURE IMPROVEMENTS (how to make it better)
---------------------------------------------------------------------
Software:
- Use MQTT to send data to a broker, then visualize with Grafana.
- Store data in InfluxDB or TimescaleDB for fast time-series queries.
- Build a small web dashboard using Plotly Dash or Streamlit.
- Add calibration routines and outlier detection (basic ML later).

Hardware:
- Real sensors: PMS5003 (PM), SCD30/SCD41 (CO2), BME280/SHT31 (T/H).
- Microcontroller: ESP32 (Wi-Fi) in a weatherproof box with a small fan.
- Power: USB adapter or solar + battery for remote spots.

The core idea is to keep barriers low, learn step by step, and scale later.
"""

# ---------------------------- IMPORTS ---------------------------------
import csv
import time
import random
from datetime import datetime

try:
    import serial  # pyserial; install with: pip install pyserial
except Exception:
    serial = None  # If not installed, we still can run in SIMULATION mode.

# ------------------------- USER SETTINGS ------------------------------
SIMULATION = True             # False → try to read from Arduino serial port
SERIAL_PORT = "COM3"          # macOS example: "/dev/tty.usbserial-1410"
BAUD_RATE = 9600
READ_INTERVAL_SEC = 1.0
CSV_PATH = "air_quality_log.csv"

# Simple, educational thresholds (WHO/EU style, simplified)
PM25_MAX = 25.0   # μg/m³ (daily guideline)
PM10_MAX  = 50.0  # μg/m³ (daily guideline)
CO2_MAX   = 1000  # ppm (ventilation comfort level)
TEMP_MIN  = -10.0 # °C
TEMP_MAX  = 45.0  # °C
HUM_MIN   = 20.0  # %
HUM_MAX   = 70.0  # %

# ----------------------- HELPER FUNCTIONS -----------------------------
def ensure_csv_header(path: str) -> None:
    """Create CSV with header if it doesn't exist."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            if f.readline().startswith("timestamp"):
                return
    except FileNotFoundError:
        pass
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "PM2_5", "PM10", "CO2", "TEMP_C", "HUM_%"])

def parse_line(line: str) -> dict:
    """Parse Arduino text line into a dictionary with floats."""
    data = {}
    for part in line.strip().split(";"):
        if not part or ":" not in part:
            continue
        key, val = part.split(":", 1)
        key = key.strip().upper()
        val = float(val.strip())
        if key in ("PM25", "PM2.5", "PM2_5"):
            data["PM2_5"] = val
        elif key == "PM10":
            data["PM10"] = val
        elif key == "CO2":
            data["CO2"] = val
        elif key in ("TEMP", "TEMPC", "T"):
            data["TEMP"] = val
        elif key in ("HUM", "RH"):
            data["HUM"] = val
    return data

def simulate_reading() -> dict:
    """Generate realistic random readings when no Arduino is connected."""
    return {
        "PM2_5": round(random.uniform(5, 80), 1),
        "PM10":  round(random.uniform(10, 120), 1),
        "CO2":   round(random.uniform(400, 2000), 0),
        "TEMP":  round(random.uniform(0, 35), 1),
        "HUM":   round(random.uniform(25, 75), 1),
    }

def connect_serial():
    """Try to open serial connection to Arduino."""
    if not serial or SIMULATION:
        return None
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Wait for board reset
        return ser
    except Exception as e:
        print(f"[Info] Could not open serial port {SERIAL_PORT}: {e}")
        return None

def evaluate_thresholds(data: dict) -> list:
    """Check if values exceed thresholds and return warnings."""
    warnings = []
    if data["PM2_5"] > PM25_MAX:
        warnings.append("Warning: PM2.5 exceeds guideline level.")
    if data["PM10"] > PM10_MAX:
        warnings.append("Warning: PM10 exceeds guideline level.")
    if data["CO2"] > CO2_MAX:
        warnings.append("Warning: CO₂ is high (ventilation recommended).")
    if not (TEMP_MIN <= data["TEMP"] <= TEMP_MAX):
        warnings.append("Warning: Temperature outside plausible range.")
    if not (HUM_MIN <= data["HUM"] <= HUM_MAX):
        warnings.append("Warning: Humidity outside comfort range.")
    return warnings

def log_csv(path: str, row: dict) -> None:
    """Append one row of data to CSV file."""
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            row["timestamp"], row["PM2_5"], row["PM10"],
            row["CO2"], row["TEMP"], row["HUM"]
        ])

# ----------------------------- MAIN -----------------------------------
def main():
    print("\nAir Quality Monitoring Framework (Helena)")
    print("Running as a framework with SIMULATION fallback.\n")
    ensure_csv_header(CSV_PATH)

    ser = connect_serial()
    print("Mode:", "SERIAL" if ser else "SIMULATION")

    try:
        while True:
            if ser:
                raw = ser.readline().decode(errors="ignore").strip()
                data = parse_line(raw) if raw else {}
            else:
                data = simulate_reading()

            if data:
                ts = datetime.now().isoformat(timespec="seconds")
                row = {
                    "timestamp": ts,
                    "PM2_5": data["PM2_5"],
                    "PM10":  data["PM10"],
                    "CO2":   data["CO2"],
                    "TEMP":  data["TEMP"],
                    "HUM":   data["HUM"],
                }

                print("\n------------------------------")
                print(ts)
                print(f"PM2.5: {row['PM2_5']} μg/m³ | PM10: {row['PM10']} μg/m³")
                print(f"CO₂: {row['CO2']} ppm | Temp: {row['TEMP']} °C | Hum: {row['HUM']} %")

                for msg in evaluate_thresholds(row):
                    print(msg)

                log_csv(CSV_PATH, row)

            time.sleep(READ_INTERVAL_SEC)

    except KeyboardInterrupt:
        print("\nStopped by user (Ctrl+C). Goodbye!")
    finally:
        if ser:
            try:
                ser.close()
            except Exception:
                pass

if __name__ == "__main__":
    main()
