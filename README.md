# VOC Biometric System

A state-of-the-class Machine Learning and Sensor-based system for Volatile Organic Compound (VOC) Biometric verification. This repository handles real-time sensor ingestion, secure data logging, and on-board model inference, supporting both **6-sensor** and **12-sensor** hardware arrays.

## Repository Structure

The project has been restructured to strictly separate machine learning training pipelines from hardware sensor interfaces.

- `src/`: Core application logic. Contains the main UI, connection code, and real-time database logging.
  - `app.py`: The entry point for the desktop application (Registration & Verification modes).
  - `sensors/`: Hardware interaction (I2C/Serial interfaces).
  - `core/`: Verification logic and ensemble models.
  - `database/`: Database insertion and logger.
  - `utils/`: Encryption / decryption tools for logs.
- `training/`: Dedicated isolated module for training ML algorithms (XGBoost, Random Forest) on collected datasets.
- `models/`: Pre-trained ONNX and pickle models consumed during runtime for inference (split into `6_sensors` and `12_sensors`).
- `data/`: SQLite databases and XML logs.

## Hardware Setup

The project supports two distinct physical arrays. It requires the following components:
1. Raspberry Pi (or compatible embedded Linux system with I2C/GPIO exposed).
2. **6 or 12 Gas/VOC Sensors** (e.g., MQ series, MEMS series) interfacing over I2C through ADS1115 ADCs.
3. Connected Fan for environment flushing.
4. Optical/IR Hand-presence sensor.

## Installation

### Dependencies

Install the required Python packages utilizing the provided `requirements.txt` file. Python 3.9+ is recommended.

```bash
pip install -r requirements.txt
```

### Configuration

Ensure your sensors are correctly wired to the hardware pins as specified in `src/sensors/sensor_reader.py` and `src/sensors/hand_controller.py`.

## Usage

### 1. Main Application (Plug and Play CLI)

To run the full biometric registration and verification cycle with live sensors, use the provided `run.sh` executable. This wrapper handles configuring the system environment to match your hardware array via the `--sensors` flag.

```bash
# Launch with a 6-sensor array
./run.sh --sensors 6

# Launch with a 12-sensor array
./run.sh --sensors 12
```

### 2. Machine Learning Pipeline (Training)

After registering new users, the models must be retrained to recognize them. Use the `train.sh` script to automate the export and training process.

```bash
# Retrain for 6-sensor configuration
./train.sh --sensors 6

# Retrain for 12-sensor configuration
./train.sh --sensors 12
```

This script will:
1. Export the latest registration features from the SQLite database to a CSV.
2. Train a full ensemble (Random Forest, Extra Trees, XGBoost, and ANN).
3. Update the models in the `models/` directory for the next app launch.

## Security & Privacy

All incoming biometric signatures are logged to an XML format which is immediately encrypted, protecting user identification vectors.
