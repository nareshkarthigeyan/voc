# Volatile Organic Compound (VOC) Biometric System

A high-fidelity hardware and machine learning framework for biometric verification using VOC sensor arrays. This system integrates real-time hardware signal processing with a multi-model ensemble for robust subject identification.

## System Architecture

The project is structured to enforce a strict separation between hardware data acquisition and machine learning optimization.

### Directory Structure
*   `src/`: Primary executable source code.
    *   `app.py`: Main GUI application entry point.
    *   `sensors/`: Low-level drivers for I2C ADCs (ADS1115), DHT11, and GPIO controllers.
    *   `core/`: High-level controllers for registration, verification, and feature extraction.
    *   `database/`: SQLite abstraction layer and secure logging utilities.
    *   `utils/`: Cryptographic tools and auxiliary dataset loaders.
*   `training/`: Isolated machine learning pipeline for offline model optimization.
*   `models/`: Directory for serialized model parameters (Pickle/Joblib), organized by sensor configuration (6 vs 12).
*   `data/`: Persistent storage for SQLite databases and encrypted XML event logs.

## Hardware Configuration

The system is designed for deployment on Raspberry Pi or equivalent Linux-based embedded platforms with I2C support.

### Requirements
1.  **Processor**: Raspberry Pi 4B or better recommended for inference latency.
2.  **ADC**: Up to three ADS1115 16-bit modules.
3.  **Sensors**: 
    *   **6-Sensor Mode**: Utilizes 2 ADS1115 modules.
    *   **12-Sensor Mode**: Utilizes 3 ADS1115 modules.
    *   **Environment**: DHT11 for temperature/humidity compensation.
4.  **Flushing**: 5V/12V Fan controlled via GPIO for sensor recovery.

## Installation and Setup

### 1. Environment Preparation
Ensure Python 3.9+ is installed. Clone the repository and install the consolidated dependency stack:

```bash
pip install -r requirements.txt
```

### 2. Hardware Wiring
Consult `src/sensors/sensor_reader.py` for specific I2C addresses (0x48, 0x49, 0x4B) and pin assignments for the DHT11 and Fan controller.

## Operational Workflow

The system operates in a three-stage pipeline: **Registration**, **Retraining**, and **Verification**.

### Stage 1: Subject Registration
Launch the application and use the GUI to register new users. Raw VOC signatures are captured, processed into feature vectors, and stored in the database.

```bash
# For 6-sensor hardware
./run.sh --sensors 6

# For 12-sensor hardware
./run.sh --sensors 12
```

### Stage 2: Model Retraining
After adding new subjects, the ML components must be optimized to recognize the expanded class set. Run the training wrapper to update the ensemble.

```bash
# Update models for the 6-sensor configuration
./train.sh --sensors 6
```
*   **Logging**: The process provides detailed feedback on data export, class distribution, and training accuracy for each ensemble member.

### Stage 3: Biometric Verification
Restart the application. The system will now load the updated neural weights and allow for real-time verification of registered subjects.

## Machine Learning Pipeline

The system utilizes a 5-model ensemble to ensure high precision and recall in variable environment conditions:

1.  **Random Forest (RF)**: Robust to outliers and high-dimensional feature noise.
2.  **Extra Trees (ET)**: Provides increased randomization to prevent overfitting on small subject cohorts.
3.  **XGBoost (XGB)**: Gradient boosted trees for capturing non-linear relationships in sensor drift.
4.  **Decision Tree (DT)**: Baseline classifier for rapid inference.
5.  **Multi-Layer Perceptron (MLP)**: A neural network component for deep feature correlation.

## Data Security and Privacy

*   **Encryption**: All VOC signatures are logged into XML format and immediately encrypted using AES-256 (via `src/utils/aes_secure.py`).
*   **Encapsulation**: Raw biometric data never leaves the local `data/` directory, ensuring user privacy in a decentralized architecture.

## Technical Support
For hardware calibration details or feature extraction mathematics, please review the documentation headers inside `src/core/feature_extractor.py`.
