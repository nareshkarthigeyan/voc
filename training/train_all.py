import os
import sys
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBClassifier
from sklearn.neural_network import MLPClassifier

def train_ensemble(csv_path, sensor_mode):
    print(f"[LOG] Training cycle initiated for SENSOR_MODE: {sensor_mode}")
    print(f"[LOG] Loading dataset from: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[ERROR] Failed to read CSV: {str(e)}")
        return

    if df.empty:
        print("[ERROR] Training failed: Dataset is empty.")
        return

    # Separate labels and features
    y = df["user_id"]
    X = df.drop(columns=["user_id", "round_no"])
    
    print(f"[LOG] Feature matrix shape: {X.shape}")
    print(f"[LOG] Label vector shape: {y.shape}")
    
    # Save feature order
    feature_order = list(X.columns)
    print(f"[LOG] Extracted {len(feature_order)} high-dimensional features.")
    
    # Encode labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    print(f"[LOG] Encoded {len(le.classes_)} classes: {list(le.classes_)}")
    
    # Scale features for MLP
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print("[LOG] Features normalized using StandardScaler.")
    
    # Define models
    models_to_train = {
        "rf_model": RandomForestClassifier(n_estimators=100, random_state=42),
        "et_model": ExtraTreesClassifier(n_estimators=100, random_state=42),
        "dt_model": DecisionTreeClassifier(random_state=42),
        "xgb_model": XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42),
        "ann_model": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
    }
    
    output_dir = os.path.join("models", f"{sensor_mode}_sensors")
    os.makedirs(output_dir, exist_ok=True)
    print(f"[LOG] Target output directory: {output_dir}")
    
    for name, model in models_to_train.items():
        print(f"[TRAIN] Fitting {name} ensemble...")
        if name == "ann_model":
            model.fit(X_scaled, y_enc)
        else:
            model.fit(X, y_enc)
        
        # Calculate training accuracy as feedback
        score = model.score(X_scaled if name == "ann_model" else X, y_enc)
        print(f"[RES] {name} trained. Training Accuracy: {score:.4f}")
        
        export_path = os.path.join(output_dir, f"{name}.pkl")
        joblib.dump(model, export_path)
        print(f"[LOG] {name} serialized to disk.")
    
    # Save Scaler and meta
    joblib.dump(scaler, os.path.join(output_dir, "ann_scaler.pkl"))
    joblib.dump(le, os.path.join(output_dir, "label_encoder.pkl"))
    joblib.dump(feature_order, os.path.join(output_dir, "feature_order.pkl"))
    
    print(f"[SUCCESS] Ensemble training complete for {sensor_mode} sensor mode.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python train_all.py <sensor_mode>")
        sys.exit(1)
        
    mode = sys.argv[1]
    csv_file = os.path.join(os.path.dirname(__file__), "training_data.csv")
    train_ensemble(csv_file, mode)
