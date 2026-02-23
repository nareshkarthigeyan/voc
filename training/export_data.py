import sqlite3
import pandas as pd
import os
import sys

# Add src to path for config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from database.config import DB_PATH

def export_to_csv(output_path):
    print(f"Connecting to database at {DB_PATH}...")
    if not os.path.exists(DB_PATH):
        print("Error: Database file not found.")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM features"
    df = pd.read_csv(conn_query(conn, query)) # Wait, pd.read_sql is better
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("Warning: No features found in database.")
        return False
        
    # Drop the auto-increment id if it exists
    if 'id' in df.columns:
        df = df.drop(columns=['id'])
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Successfully exported {len(df)} samples to {output_path}")
    return True

if __name__ == "__main__":
    csv_out = os.path.join(os.path.dirname(__file__), "training_data.csv")
    export_to_csv(csv_out)
