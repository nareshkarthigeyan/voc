import joblib
import numpy as np
import os
import time
from Database.user_dao import get_user_name
from Fan_controller import FanController



from pathlib import Path

SENSOR_MODE = int(os.environ.get("VOC_SENSOR_MODE", "6"))
MODELS_DIR = Path(__file__).parent.parent.parent / "models" / f"{SENSOR_MODE}_sensors"

rf_model  = joblib.load(os.path.join(MODELS_DIR, "rf_model.pkl"))
et_model  = joblib.load(os.path.join(MODELS_DIR, "et_model.pkl"))
dt_model  = joblib.load(os.path.join(MODELS_DIR, "dt_model.pkl"))
xgb_model = joblib.load(os.path.join(MODELS_DIR, "xgb_model.pkl"))
ann_model = joblib.load(os.path.join(MODELS_DIR, "ann_model.pkl"))
ann_scaler = joblib.load(os.path.join(MODELS_DIR, "ann_scaler.pkl"))

label_encoder = joblib.load(os.path.join(MODELS_DIR, "label_encoder.pkl"))
feature_order = joblib.load(os.path.join(MODELS_DIR, "feature_order.pkl"))

FLUSH_DURATION = 30


# ---------------- FAN FLUSH ----------------
def flush_chamber():
    print("\n[INFO] Waiting for hand removal before flushing...")
    fan = FanController()

    fan.flush(FLUSH_DURATION)

    print("[INFO] Flushing completed\n")


# ---------------- VERIFICATION ----------------
def verify_user(round_feature_list):

    all_round_probs = []
    detailed_votes = []

    for round_idx, feature_dict in enumerate(round_feature_list):

        X = np.array([[feature_dict.get(f, 0.0) for f in feature_order]])

        probs = {}

        probs["RF"]  = rf_model.predict_proba(X)[0]
        probs["ET"]  = et_model.predict_proba(X)[0]
        probs["DT"]  = dt_model.predict_proba(X)[0]
        probs["XGB"] = xgb_model.predict_proba(X)[0]

        X_scaled = ann_scaler.transform(X)
        probs["ANN"] = ann_model.predict_proba(X_scaled)[0]

        # Average model probabilities for this round
        round_prob = np.mean(list(probs.values()), axis=0)
        all_round_probs.append(round_prob)

        # Store detailed model votes
        round_vote = {}
        for model_name, prob in probs.items():
            idx = np.argmax(prob)
            name = label_encoder.inverse_transform([idx])[0]
            conf = round(float(prob[idx] * 100), 2)

            round_vote[model_name] = {
                "user_name": name,
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

    #final_name = label_encoder.inverse_transform([final_index])[0]
    predict_user_id = label_encoder.inverse_transform([final_index])[0]
    predict_user_name = get_user_name(predict_user_id)
    
    status = "VERIFIED" if final_confidence >= 70 else "NOT VERIFIED"

    result = {
        "status": status,
        "user_name": predict_user_name if status=="VERIFIED" else None,
        "user_id": predict_user_id,
        "confidence": final_confidence,
        "round_details": detailed_votes
    }

    # FAN FLUSH AFTER VERIFICATION
    flush_chamber()

    return result

