import sqlite3
import pandas as pd
import os
import sys

# Add src to path for config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from database.config import DB_PATH

def export_to_csv(output_path):
    print(f"[LOG] Initializing data export sequence...")
    print(f"[LOG] Target database: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database file not found at {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        print(f"[LOG] Connection established to SQLite database.")
        
        query = "SELECT * FROM features"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print("[WARNING] The 'features' table is empty. No data to export.")
            return False
            
        print(f"[LOG] Successfully retrieved {len(df)} records from 'features' table.")
        
        # Drop the auto-increment id if it exists
        if 'id' in df.columns:
            df = df.drop(columns=['id'])
            print("[LOG] Primary key 'id' column dropped for training compatibility.")
        
        # Log unique users found
        if 'user_id' in df.columns:
            unique_users = df['user_id'].unique()
            print(f"[LOG] Dataset includes {len(unique_users)} unique subjects: {list(unique_users)}")
    
        # Save to CSV
        df.to_csv(output_path, index=False)
        print(f"[LOG] Data serialization complete. Path: {output_path}")
        return True
    except Exception as e:
        print(f"[CRITICAL] Export failed due to system error: {str(e)}")
        return False

if __name__ == "__main__":
    csv_out = os.path.join(os.path.dirname(__file__), "training_data.csv")
    export_to_csv(csv_out)
