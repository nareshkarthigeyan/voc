import joblib
import numpy as np
import os
import time
from database.user_dao import get_user_name
from sensors.fan_controller import FanController



from pathlib import Path

SENSOR_MODE = int(os.environ.get("VOC_SENSOR_MODE", "6"))
MODELS_DIR = Path(__file__).parent.parent.parent / "models" / f"{SENSOR_MODE}_sensors"

def load_latest_models():
    """Dynamically load models to ensure we fetch the latest trained weights and clear cache."""
    return {
        "rf": joblib.load(os.path.join(MODELS_DIR, "rf_model.pkl")),
        "et": joblib.load(os.path.join(MODELS_DIR, "et_model.pkl")),
        "dt": joblib.load(os.path.join(MODELS_DIR, "dt_model.pkl")),
        "xgb": joblib.load(os.path.join(MODELS_DIR, "xgb_model.pkl")),
        "ann": joblib.load(os.path.join(MODELS_DIR, "ann_model.pkl")),
        "scaler": joblib.load(os.path.join(MODELS_DIR, "ann_scaler.pkl")),
        "le": joblib.load(os.path.join(MODELS_DIR, "label_encoder.pkl")),
        "order": joblib.load(os.path.join(MODELS_DIR, "feature_order.pkl"))
    }

FLUSH_DURATION = 30


# ---------------- FAN FLUSH ----------------
def flush_chamber():
    print("\n[INFO] Waiting for hand removal before flushing...")
    fan = FanController()

    fan.flush(FLUSH_DURATION)

    print("[INFO] Flushing completed\n")


# ---------------- VERIFICATION ----------------
def verify_user(round_feature_list):
    models = load_latest_models()
    all_round_probs = []
    detailed_votes = []

    for round_idx, feature_dict in enumerate(round_feature_list):

        X = np.array([[feature_dict.get(f, 0.0) for f in models["order"]]])

        probs = {}

        probs["RF"]  = models["rf"].predict_proba(X)[0]
        probs["ET"]  = models["et"].predict_proba(X)[0]
        probs["DT"]  = models["dt"].predict_proba(X)[0]
        probs["XGB"] = models["xgb"].predict_proba(X)[0]

        X_scaled = models["scaler"].transform(X)
        probs["ANN"] = models["ann"].predict_proba(X_scaled)[0]

        # Average model probabilities for this round
        round_prob = np.mean(list(probs.values()), axis=0)
        all_round_probs.append(round_prob)

        # Store detailed model votes
        round_vote = {}
        for model_name, prob in probs.items():
            idx = np.argmax(prob)
            conf = round(float(prob[idx] * 100), 2)

            if conf >= 70:
                model_pred_id = models["le"].inverse_transform([idx])[0]
                model_pred_name = get_user_name(model_pred_id) or "Unknown Name"
                user_label = f"{model_pred_name} (ID: {model_pred_id})"
            else:
                user_label = "No Data Found"
                
            round_vote[model_name] = {
                "user_name": user_label,
                "confidence": conf
            }

        detailed_votes.append({
            "round": round_idx + 1,
            "votes": round_vote
        })

    # Final fusion across all rounds
    fused_prob = np.mean(all_round_probs, axis=0)

    final_index = np.argmax(fused_prob)
    final_confidence = round(float(fused_prob[final_index] * 100), 2)

    #final_name = models["le"].inverse_transform([final_index])[0]
    predict_user_id = models["le"].inverse_transform([final_index])[0]
    predict_user_name = get_user_name(predict_user_id) or f"Unknown Name"
    
    status = "VERIFIED" if final_confidence >= 70 else "NOT VERIFIED"

    if status == "NOT VERIFIED":
        predict_user_name = "No Data Found"
        predict_user_id = "No Data Found"

    result = {
        "status": status,
        "user_name": predict_user_name,
        "user_id": predict_user_id,
        "confidence": final_confidence,
        "round_details": detailed_votes
    }

    # FAN FLUSH AFTER VERIFICATION
    flush_chamber()

    return result

