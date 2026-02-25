import sqlite3
from datetime import datetime
from database.config import DB_PATH


def insert_user(user_id, user_name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Ensure users table exists (backward compatibility)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            registered_at TEXT
        )
    """)

    # Add registered_at column if table was created without it (old schema)
    try:
        cur.execute("ALTER TABLE users ADD COLUMN registered_at TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    cur.execute("""
        INSERT OR REPLACE INTO users (user_id, name, registered_at)
        VALUES (?, ?, ?)
    """, (user_id, user_name, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT user_id, name FROM users")
    rows = cur.fetchall()

    conn.close()
    return rows


def get_user_name(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT name FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    conn.close()
    
    if row:
        return row[0]
    return None
