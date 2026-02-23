# VOC Biometric System

A state-of-the-class Machine Learning and Sensor-based system for Volatile Organic Compound (VOC) Biometric verification. This repository handles real-time sensor ingestion, secure data logging, and on-board model inference, specifically configured for a 6-sensor hardware setup.

## Repository Structure

The project has been restructured to strictly separate machine learning training pipelines from hardware sensor interfaces.

- `src/`: Core application logic. Contains the main UI, 6-sensor connection code, and real-time database logging.
  - `app.py`: The entry point for the desktop application (Registration & Verification modes).
  - `sensors/`: Hardware interaction (I2C/Serial interfaces).
  - `core/`: Verification logic and ensemble models.
  - `database/`: Database insertion and logger.
  - `utils/`: Encryption / decryption tools for logs.
- `training/`: Dedicated isolated module for training ML algorithms (XGBoost, Random Forest) on collected datasets.
- `models/`: Pre-trained ONNX models consumed during runtime for inference.
- `data/`: SQLite databases and XML logs.

## Hardware Setup (6 Sensors)

The project requires the following components:
1. Raspberry Pi (or compatible embedded Linux system with I2C/GPIO exposed).
2. 6 Gas/VOC Sensors (e.g., MQ series, BME688, SGP40 depending on exact implementation) interfacing over Analog/I2C.
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

### 1. Main Application (Plug and Play)

To run the full biometric registration and verification cycle with live sensors:

```bash
cd src
python app.py
```

### 2. Machine Learning Pipeline

Model training is conducted offline. Use the `training/` module to update the models based on aggregated user data.

```bash
cd training
python train_ann.py
```

Model export scripts (e.g., `Export_models_to_ONNX.py`) are placed here to export parameters into the `models/` directory for application inference.

## Security & Privacy

All incoming biometric signatures are logged to an XML format which is immediately encrypted, protecting user identification vectors.
