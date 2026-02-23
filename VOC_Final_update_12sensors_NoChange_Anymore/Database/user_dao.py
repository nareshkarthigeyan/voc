import sqlite3
from datetime import datetime
from Database.db_init import DB_PATH


def insert_user(user_id, user_name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO users (user_id, user_name, registered_at)
        VALUES (?, ?, ?)
    """, (user_id, user_name, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT user_id, user_name FROM users")
    rows = cur.fetchall()

    conn.close()
    return rows
