#!/bin/bash

# Default to 6 sensors if not provided
SENSOR_MODE=6

# Parse CLI arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --sensors) SENSOR_MODE="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [[ "$SENSOR_MODE" != "6" && "$SENSOR_MODE" != "12" ]]; then
    echo "Error: --sensors must be either 6 or 12"
    exit 1
fi

echo "[SYSTEM] VOC Training Pipeline Initialized"
echo "[SYSTEM] Configuration: ${SENSOR_MODE}-Sensor Array"

# Ensure we are in the project root
cd "$(dirname "$0")" || exit

# 1. Export Data
echo "[STEP 1/2] Data Acquisition: Exporting registration features from SQL to CSV..."
python3 training/export_data.py

if [ $? -ne 0 ]; then
    echo "[CRITICAL] Data acquisition failed. Training terminated."
    exit 1
fi

# 2. Train Models
echo "[STEP 2/2] Learning Phase: Firing ensemble training (RF, ET, DT, XGB, ANN)..."
python3 training/train_all.py $SENSOR_MODE

if [ $? -ne 0 ]; then
    echo "[CRITICAL] Model optimization failed. Check logs for details."
    exit 1
fi

echo "[SUCCESS] Pipeline execution finished. Neural weights and ensemble parameters updated."
echo "[INFO] Target Directory: models/${SENSOR_MODE}_sensors/"
