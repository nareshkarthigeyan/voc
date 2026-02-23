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
    print(f"Loading training data for {sensor_mode} sensor mode...")
    df = pd.read_csv(csv_path)
    
    if df.empty:
        print("Error: Empty training data.")
        return

    # Separate labels and features
    y = df["user_id"]
    X = df.drop(columns=["user_id", "round_no"])
    
    # Save feature order
    feature_order = list(X.columns)
    
    # Encode labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    
    # Scale features for MLP
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
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
    
    for name, model in models_to_train.items():
        print(f"Training {name}...")
        if name == "ann_model":
            model.fit(X_scaled, y_enc)
        else:
            model.fit(X, y_enc)
        joblib.dump(model, os.path.join(output_dir, f"{name}.pkl"))
    
    # Save Scaler and meta
    joblib.dump(scaler, os.path.join(output_dir, "ann_scaler.pkl"))
    joblib.dump(le, os.path.join(output_dir, "label_encoder.pkl"))
    joblib.dump(feature_order, os.path.join(output_dir, "feature_order.pkl"))
    
    print(f"✅ All models trained and saved to {output_dir}")
    
    print(f"✅ All models trained and saved to {output_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python train_all.py <sensor_mode>")
        sys.exit(1)
        
    mode = sys.argv[1]
    csv_file = os.path.join(os.path.dirname(__file__), "training_data.csv")
    train_ensemble(csv_file, mode)
