import sqlite3

from database.config import DB_PATH


def store_features(user_id, feature_dict, round_no):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    columns = list(feature_dict.keys())
    values = [float(feature_dict[col]) for col in columns]
    placeholders = ",".join(["?"] * (len(values) + 2))

    query = f"""
        INSERT INTO features
        (user_id, round_no, {",".join(columns)})
        VALUES ({placeholders})
    """
    cur.execute(query, [user_id, round_no] + values)
    conn.commit()
    conn.close()

def store_feedback(user_id, predicted_id, predicted_name, confidence, reward, feature_dict):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    columns = list(feature_dict.keys())
    values = [float(feature_dict[col]) for col in columns]
    placeholders = ",".join(["?"] * (len(values) + 5))
    
    from datetime import datetime
    timestamp = datetime.now().isoformat()

    query = f"""
        INSERT INTO feedback_buffer
        (user_id, predicted_id, predicted_name, confidence, reward, timestamp, {",".join(columns)})
        VALUES ({placeholders})
    """
    
    cur.execute(query, [user_id, predicted_id, predicted_name, confidence, reward, timestamp] + values)
    conn.commit()
    conn.close()

def store_radar_profile(user_id, user_name, radar_plot_path, registration_readings):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS radar_profiles (
            user_id TEXT PRIMARY KEY,
            user_name TEXT,
            radar_plot_path TEXT,
            registration_readings TEXT
        )
    """)
    
    import json
    readings_json = json.dumps(registration_readings)
    
    cur.execute("""
        INSERT OR REPLACE INTO radar_profiles 
        (user_id, user_name, radar_plot_path, registration_readings)
        VALUES (?, ?, ?, ?)
    """, (user_id, user_name, radar_plot_path, readings_json))
    
    conn.commit()
    conn.close()

def get_radar_profile(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Ensure table exists (backward compatibility with old databases)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS radar_profiles (
            user_id TEXT PRIMARY KEY,
            user_name TEXT,
            radar_plot_path TEXT,
            registration_readings TEXT
        )
    """)
    
    cur.execute("SELECT user_name, radar_plot_path, registration_readings FROM radar_profiles WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    
    if row:
        import json
        return {
            "user_name": row[0],
            "radar_plot_path": row[1],
            "registration_readings": json.loads(row[2])
        }
    return None

