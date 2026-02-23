import pandas as pd
import joblib

def load_training_data(csv_path, scaler_path):
    df = pd.read_csv(csv_path)

    y = df["user_id"]                # label
    X = df.drop(columns=["user_id"]) # features

    scaler = joblib.load(scaler_path)
    X_scaled = scaler.transform(X)

    return X_scaled, y
