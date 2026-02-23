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
