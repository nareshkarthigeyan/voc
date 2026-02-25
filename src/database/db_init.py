"""
Non-destructive database initializer.
Creates all tables if they don't exist. Safe to run multiple times.
"""
import sqlite3
import os
from database.config import DB_PATH
from core.feature_extractor import extract_features


def init_db(feature_columns=None):
    """Initialize all database tables non-destructively (CREATE IF NOT EXISTS)."""
    
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── Users Table ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            registered_at TEXT
        )
    """)

    # ── Features Table ──
    if feature_columns:
        columns_sql = ", ".join([f"{col} REAL" for col in feature_columns])
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                round_no INTEGER,
                {columns_sql},
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        
        # ── Reinforcement Feedback Replay Buffer ──
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS feedback_buffer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                predicted_id TEXT,
                predicted_name TEXT,
                confidence REAL,
                reward INTEGER,
                timestamp TEXT,
                {columns_sql},
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)

    # ── Radar Profiles Table ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS radar_profiles (
            user_id TEXT PRIMARY KEY,
            user_name TEXT,
            radar_plot_path TEXT,
            registration_readings TEXT
        )
    """)

    conn.commit()
    conn.close()
    print(f"[DB] All tables initialized (non-destructive) at {DB_PATH}")


def ensure_all_tables():
    """Quick call to ensure every table exists. Safe to call at startup."""
    # Generate feature columns from a dummy sample
    dummy_sample = [{
        "mq6_1": 0.0,
        "mq135_1": 0.0,
        "mq137_1": 0.0,
        "mems_nh3_1": 0.0,
        "mems_ethanol_1": 0.0,
        "mems_odor_1": 0.0,
    }]
    feature_dict = extract_features(dummy_sample)
    feature_columns = list(feature_dict.keys())
    init_db(feature_columns)


if __name__ == "__main__":
    ensure_all_tables()
    print("[DB] Database initialization complete.")
