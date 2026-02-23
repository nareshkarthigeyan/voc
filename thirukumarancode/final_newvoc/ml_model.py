# ml_model.py
import os
import joblib
import xml.etree.ElementTree as ET
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler

# Optional XGBoost
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

# ===== Config =====
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)
XML_FILE = "users.xml"

CLASSIFIERS = {
    "Random Forest": RandomForestClassifier(n_estimators=100),
    "SVM": SVC(probability=True),
    "Decision Tree": DecisionTreeClassifier(),
    "Logistic Regression": LogisticRegression(max_iter=500),
    "Nearest Neighbour": KNeighborsClassifier(),
}

if HAS_XGBOOST:
    CLASSIFIERS["XGBoost"] = xgb.XGBClassifier(eval_metric="mlogloss")

FEATURES = [
    "mq6_1", "mq135_1", "mq137_1",
    "mq6_2", "mq135_2", "mq137_2",
    "mems_nh3_1", "mems_ethanol_1", "mems_odor_1",
    "mems_nh3_2", "mems_ethanol_2", "mems_odor_2",
    "dht_temp", "dht_hum"
]

# ====== XML Helper ======
def append_voc_to_user(user_id, voc_data):
    """Add new VOC data to existing or new user in XML"""
    if not os.path.exists(XML_FILE):
        root = ET.Element("users")
        tree = ET.ElementTree(root)
        tree.write(XML_FILE)

    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    user = root.find(f"./user[@user_id='{user_id}']")
    if user is None:
        user = ET.SubElement(root, "user", {"user_id": str(user_id)})
    voc_elem = ET.SubElement(user, "voc")
    for f in FEATURES:
        val_elem = ET.SubElement(voc_elem, f)
        val_elem.text = str(voc_data.get(f, 0))
    tree.write(XML_FILE)

# ====== Training ======
def train_all_with_logs():
    """Train all classifiers on all users in XML"""
    if not os.path.exists(XML_FILE):
        print("❌ users.xml not found.")
        return

    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    X, y = [], []

    # Collect all VOC data
    for user in root.findall("user"):
        user_id = user.get("user_id") or user.get("id") or user.get("uid")
        if not user_id:
            continue
        for voc in user.findall("voc"):
            sample = [float(voc.find(f).text) if voc.find(f) is not None else 0 for f in FEATURES]
            X.append(sample)
            y.append(user_id)

    if len(X) == 0:
        print("⚠️ No VOC data found. Cannot train models.")
        return

    X = np.array(X)
    y = np.array(y)

    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, os.path.join(MODEL_DIR, "VOC_scaler.pkl"))

    # Train classifiers
    for clf_name, clf in CLASSIFIERS.items():
        try:
            if clf_name == "XGBoost":
                le = LabelEncoder()
                y_encoded = le.fit_transform(y)
                clf.fit(X_scaled, y_encoded)
                joblib.dump(clf, os.path.join(MODEL_DIR, "XGBoost_model.pkl"))
                joblib.dump(le, os.path.join(MODEL_DIR, "XGBoost_label_encoder.pkl"))
            else:
                clf.fit(X_scaled, y)
                joblib.dump(clf, os.path.join(MODEL_DIR, f"{clf_name.replace(' ','_')}_model.pkl"))
            print(f"✅ {clf_name} model trained for {len(np.unique(y))} users.")
        except Exception as e:
            print(f"❌ Training failed for {clf_name}: {e}")

# ====== Prediction ======
def predict_user(voc_data, classifier="Random Forest", confidence_threshold=0.5):
    """Predict user ID from VOC data"""
    model_file = os.path.join(MODEL_DIR, f"{classifier.replace(' ','_')}_model.pkl")
    scaler_file = os.path.join(MODEL_DIR, "VOC_scaler.pkl")
    if not os.path.exists(model_file) or not os.path.exists(scaler_file):
        raise ValueError(f"Model or scaler not found. Train first.")

    clf = joblib.load(model_file)
    scaler = joblib.load(scaler_file)
    X_input = np.array([[float(voc_data.get(f,0)) for f in FEATURES]])
    X_scaled = scaler.transform(X_input)

    if classifier == "XGBoost":
        le_file = os.path.join(MODEL_DIR, "XGBoost_label_encoder.pkl")
        le = joblib.load(le_file)
        pred_encoded = clf.predict(X_scaled)
        predicted_id = le.inverse_transform(pred_encoded)[0]
        probabilities = clf.predict_proba(X_scaled)[0]
    else:
        predicted_id = clf.predict(X_scaled)[0]
        probabilities = clf.predict_proba(X_scaled)[0] if hasattr(clf, "predict_proba") else [1.0]

    max_conf = max(probabilities)
    print("VOC Prediction ID:", predicted_id)
    print("Probabilities:", probabilities)
    print("Max confidence:", max_conf)

    if max_conf >= confidence_threshold:
        return predicted_id
    return None

# ===== CLI =====
if __name__ == "__main__":
    train_all_with_logs()
