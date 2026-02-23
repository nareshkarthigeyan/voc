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

echo "--- VOC Training Pipeline ---"
echo "Target: ${SENSOR_MODE}-Sensor Mode"

# 1. Export Data
echo "[1/2] Exporting current database to CSV..."
python3 training/export_data.py

if [ $? -ne 0 ]; then
    echo "❌ Export failed. Aborting."
    exit 1
fi

# 2. Train Models
echo "[2/2] Training ensemble models (RF, ET, DT, XGB, ANN)..."
python3 training/train_all.py $SENSOR_MODE

if [ $? -ne 0 ]; then
    echo "❌ Training failed."
    exit 1
fi

echo "✅ Training complete. Models updated in models/${SENSOR_MODE}_sensors/"
