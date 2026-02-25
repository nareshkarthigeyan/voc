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
        
        # RLHF: Experience Replay & Oversampling from Feedback Buffer
        try:
            fb_query = "SELECT * FROM feedback_buffer"
            fb_df = pd.read_sql_query(fb_query, conn)
            
            if not fb_df.empty:
                print(f"[LOG] RLHF: Found {len(fb_df)} human-corrected feedback samples.")
                # Drop tracking columns to align schema with `features`
                cols_to_drop = ['id', 'predicted_id', 'predicted_name', 'confidence', 'reward', 'timestamp']
                fb_df_clean = fb_df.drop(columns=[col for col in cols_to_drop if col in fb_df.columns], errors='ignore')
                
                # Assign a synthetic 'round_no' if it is missing (as feedback buffer doesn't explicitly guarantee ordering tracking)
                if 'round_no' in df.columns and 'round_no' not in fb_df_clean.columns:
                    fb_df_clean['round_no'] = 1 
                    
                # Oversample 5x to increase decision-boundary importance (Weighted Retraining)
                oversampled_fb = pd.concat([fb_df_clean] * 5, ignore_index=True)
                
                # Prevent alignment issues before concat
                if 'id' in df.columns:
                    df = df.drop(columns=['id'])
                
                df = pd.concat([df, oversampled_fb], ignore_index=True)
                print(f"[LOG] RLHF: Appended {len(oversampled_fb)} weighted feedback loops to the training buffer.")
        except Exception as e:
            print(f"[WARNING] RLHF Replay Buffer query skipped or failed: {str(e)}")
            
        conn.close()
        
        if df.empty:
            print("[WARNING] The 'features' dataset is completely empty. No data to export.")
            return False
            
        print(f"[LOG] Successfully compiled {len(df)} total training vectors for the ANN pipeline.")
        
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
