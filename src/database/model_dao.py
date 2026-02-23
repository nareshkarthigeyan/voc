import sqlite3
import numpy as np
from database.config import DB_PATH


def insert_kmeans_model(user_id, centroid, threshold):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    centroid_blob = centroid.astype(np.float32).tobytes()

    cur.execute("""
        INSERT OR REPLACE INTO kmeans_models (user_id, centroid, threshold)
        VALUES (?, ?, ?)
    """, (user_id, centroid_blob, float(threshold)))

    conn.commit()
    conn.close()


def get_kmeans_model(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT centroid, threshold
        FROM kmeans_models
        WHERE user_id = ?
    """, (user_id,))

    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    centroid = np.frombuffer(row[0], dtype=np.float32)
    threshold = row[1]

    return centroid, threshold
