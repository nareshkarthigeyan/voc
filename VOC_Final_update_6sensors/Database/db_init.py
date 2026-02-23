from Features.feature_extractor import extract_features

DB_PATH = "/home/voc12/Desktop/VOC_updated_New6/voc_biometrics.db"
def init_db(feature_columns):
    import sqlite3

    conn = sqlite3.connect("voc_biometrics.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT
        )
    """)

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

    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    # Generate dummy feature dict to extract column names
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
    print("Database created successfully with", len(feature_columns), "feature columns.")
