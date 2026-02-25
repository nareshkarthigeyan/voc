import os
import shutil
import sys
from pathlib import Path

def reset_environment():
    print("[WARNING] Initiating Complete System Data Reset...")
    base_dir = Path(__file__).parent
    
    # 1. Delete SQLite Database
    db_path = base_dir / "data" / "voc_biometrics.db"
    if db_path.exists():
        os.remove(db_path)
        print(f"  [DELETED] Database removed: {db_path}")
    else:
        print(f"  [SKIP] Database not found: {db_path}")
        
    # 2. Delete Training CSV
    csv_path = base_dir / "training" / "training_data.csv"
    if csv_path.exists():
        os.remove(csv_path)
        print(f"  [DELETED] Exported dataset removed: {csv_path}")
    else:
        print(f"  [SKIP] Dataset not found: {csv_path}")
        
    # 3. Delete Models Directory (containing serialized pkl files)
    models_dir = base_dir / "models"
    if models_dir.exists() and models_dir.is_dir():
        shutil.rmtree(models_dir)
        print(f"  [DELETED] Neural Network & Ensemble models removed: {models_dir}")
    else:
        print(f"  [SKIP] Models directory not found: {models_dir}")
        
    print("\n[SUCCESS] System reset complete.")
    print("You may now launch the GUI and begin registering minimum 3 new users at 1,500 samples each.")
    
    # Optionally initialize a blank database
    sys.path.append(str(base_dir / "src"))
    try:
        from database.db_init import ensure_all_tables
        ensure_all_tables()
        print("[SUCCESS] Blank database structure initialized.")
    except Exception as e:
        print(f"[WARN] Could not pre-initialize empty tables: {e}")

if __name__ == "__main__":
    confirm = input("Are you SURE you want to irreversibly wipe all users, training data, and ML models? (y/N): ")
    if confirm.lower() == 'y':
        reset_environment()
    else:
        print("Data reset aborted.")
