import time
import uuid
import numpy as np
import sqlite3

from sensors.sensor_reader import VOCSensor
from features.feature_extractor import extract_features

from database.user_dao import insert_user
from database.feature_dao import insert_features
from database.model_dao import insert_kmeans_model

from utils.secure_voc_logger import log_user_data
from core.verification_controller import generate_embedding

from sensors.Fan_controller import FanController


import os

SENSOR_MODE = int(os.environ.get("VOC_SENSOR_MODE", "6"))
NUM_ROUNDS = 6 if SENSOR_MODE == 12 else 10
ROUND_DELAY = 20
RETRY_DELAY = 5
FLUSH_DURATION = 30


# ---------------- FAN FLUSH ----------------
def flush_chamber():
    print("\n[INFO] Waiting for hand removal before flushing...")

    fan = FanController()   # SAME LOGIC AS VERIFICATION

    fan.flush(FLUSH_DURATION)

    print("[INFO] Flushing completed\n")


def safe_sensor_read(sensor):
    try:
        status, voc, _ = sensor.read_sensors()

        if status != "OK":
            return None

        return voc

    except Exception as e:
        print("[SENSOR ERROR]", e)
        print("[INFO] Waiting for sensors to stabilize...")
        time.sleep(RETRY_DELAY)
        return None


def register_user(user_name: str, extra_biometrics: dict | None = None):

    print("[INFO] Starting registration")

    user_id = str(uuid.uuid4())[:8]
    sensor = VOCSensor()
    voc_samples = []

    print(f"[INFO] Collecting {NUM_ROUNDS} rounds...")

    for round_idx in range(NUM_ROUNDS):

        print(f"[INFO] Round {round_idx + 1}/{NUM_ROUNDS}")

        voc_data = safe_sensor_read(sensor)

        if voc_data is None:
            print("[WARNING] Skipping this round")
            continue

        clean_data = {
            k: float(v) if v is not None and np.isfinite(v) else 0.0
            for k, v in voc_data.items()
        }

        voc_samples.append(clean_data)

        if round_idx < NUM_ROUNDS - 1:
            time.sleep(ROUND_DELAY)

    if not voc_samples:
        raise RuntimeError("No valid sensor data captured")

    print("[INFO] Extracting features...")
    feature_vector = extract_features(voc_samples)

    embedding = generate_embedding(feature_vector)

    conn = sqlite3.connect("voc_biometrics.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO embeddings (user_id, embedding)
        VALUES (?, ?)
    """, (user_id, embedding.astype(np.float32).tobytes()))

    conn.commit()
    conn.close()

    print("[INFO] Storing user & features in DB...")
    insert_user(user_id, user_name)
    insert_features(user_id, feature_vector)

    try:
        from sklearn.cluster import KMeans

        X = np.array(list(feature_vector.values()), dtype=float).reshape(1, -1)
        kmeans = KMeans(n_clusters=1, random_state=42).fit(X)

        insert_kmeans_model(user_id, kmeans.cluster_centers_[0], 0.0)

    except Exception:
        print("[INFO] Skipping local KMeans")

    log_payload = {"voc": voc_samples}

    if extra_biometrics:
        log_payload.update(extra_biometrics)

    log_user_data(
        user_id=user_id,
        user_name=user_name,   # FIXED (you had name variable error)
        data=log_payload
    )

    print("\n[SUCCESS] Registration complete")
    print("User ID:", user_id)

    # 🔥 SAME AS VERIFICATION
    flush_chamber()

    return user_id