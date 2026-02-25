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

export VOC_SENSOR_MODE=$SENSOR_MODE

echo "Starting VOC Biometric System in ${SENSOR_MODE}-Sensor Mode..."

# Navigate to source code directory
cd "$(dirname "$0")/src" || exit

# Non-destructive database initialization (creates missing tables without destroying data)
echo "[INIT] Ensuring all database tables exist..."
python3 -c "from database.db_init import ensure_all_tables; ensure_all_tables()"

# Launch app
python3 app.py
