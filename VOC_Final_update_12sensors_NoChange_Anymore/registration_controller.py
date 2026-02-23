import time
import uuid
import numpy as np
import sqlite3

from sensors.sensor_reader import VOCSensor
from features.feature_extractor import extract_features

from database.user_dao import insert_user
from database.feature_dao import insert_features
from database.model_dao import insert_kmeans_model

from secure_voc_logger import log_user_data
from verification_controller import generate_embedding

from hand_controller import HandController
from Fan_controller import FanController   # 🔥 IMPORT FAN


# -------- CONFIG --------
NUM_ROUNDS = 10
ROUND_DELAY = 20
RETRY_DELAY = 5
FLUSH_DURATION = 20


def safe_sensor_read(sensor):
    """
    Safe read wrapper to prevent crashes.
    """
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


def flush_chamber():
    """
    Turn ON fan for flushing after hand removal.
    """
    print("\n[INFO] Waiting for hand removal before flushing...")

    hand = HandController()
    fan = FanController()

    # Wait until hand removed
    while hand.hand_present():
        time.sleep(0.2)

    print("[INFO] Starting flushing for 20 seconds...")
    fan.flush(FLUSH_DURATION)

    print("[INFO] Flushing completed\n")


def register_user(user_name: str, extra_biometrics: dict | None = None):

    print("[INFO] Starting registration")

    user_id = str(uuid.uuid4())[:8]
    sensor = VOCSensor()

    voc_samples = []

    # -------- ROUND ROBIN SAMPLING --------
    print(f"[INFO] Collecting {NUM_ROUNDS} rounds with {ROUND_DELAY}s delay...")

    for round_idx in range(NUM_ROUNDS):

        print(f"[INFO] Round {round_idx + 1}/{NUM_ROUNDS}")

        voc_data = safe_sensor_read(sensor)

        if voc_data is None:
            print("[WARNING] Skipping this round due to sensor failure")
            continue

        # SANITIZE immediately
        clean_data = {
            k: float(v) if v is not None and np.isfinite(v) else 0.0
            for k, v in voc_data.items()
        }

        voc_samples.append(clean_data)

        if round_idx < NUM_ROUNDS - 1:
            print(f"[INFO] Waiting {ROUND_DELAY} seconds...")
            time.sleep(ROUND_DELAY)

    if not voc_samples:
        raise RuntimeError("No valid sensor data captured")

    # -------- FEATURE EXTRACTION --------
    print("[INFO] Extracting features...")
    feature_vector = extract_features(voc_samples)

    # -------- EMBEDDING STORAGE --------
    embedding = generate_embedding(feature_vector)

    conn = sqlite3.connect("voc_biometrics.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO embeddings (user_id, embedding)
        VALUES (?, ?)
    """, (user_id, embedding.astype(np.float32).tobytes()))
    conn.commit()
    conn.close()

    # -------- DATABASE STORAGE --------
    print("[INFO] Storing user & features in DB...")
    insert_user(user_id, user_name)
    insert_features(user_id, feature_vector)

    # -------- OPTIONAL SMALL LOCAL MODEL --------
    try:
        from sklearn.cluster import KMeans

        X = np.array(list(feature_vector.values()), dtype=float).reshape(1, -1)
        kmeans = KMeans(n_clusters=1, random_state=42).fit(X)

        centroid = kmeans.cluster_centers_[0]
        threshold = 0.0

        insert_kmeans_model(user_id, centroid, threshold)

    except Exception:
        print("[INFO] Skipping local KMeans training")

    # -------- ENCRYPTED XML LOG --------
    log_payload = {"voc": voc_samples}

    if extra_biometrics:
        log_payload.update(extra_biometrics)

    log_user_data(
        user_id=user_id,
        user_name=user_name,
        data=log_payload
    )

    print("\n[SUCCESS] Registration complete")
    print("User ID:", user_id)

    # 🔥 FAN FLUSH AFTER REGISTRATION
    flush_chamber()

    return user_id


# -------- CLI TEST --------
if __name__ == "__main__":
    name = input("Enter user name: ").strip()
    register_user(name)
