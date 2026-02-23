import sqlite3
import pandas as pd

DB_PATH = "voc_biometrics.db"
OUTPUT_EXCEL = "voc_biometrics.xlsx"

conn = sqlite3.connect(DB_PATH)

# Get all table names
tables = pd.read_sql(
    "SELECT name FROM sqlite_master WHERE type='table';",
    conn
)["name"].tolist()

with pd.ExcelWriter(OUTPUT_EXCEL, engine="xlsxwriter") as writer:
    for table in tables:
        df = pd.read_sql(f"SELECT * FROM {table}", conn)
        df.to_excel(writer, sheet_name=table, index=False)
        print(f"[OK] Exported table: {table}")

conn.close()

print(f"\n✅ Database exported to {OUTPUT_EXCEL}")
