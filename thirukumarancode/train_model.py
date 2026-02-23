# train_model.py
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

MODEL_DIR = "models"
LOG_FILE = "voc_log.xml"
os.makedirs(MODEL_DIR, exist_ok=True)

CLASSIFIERS = {
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
    "SVM": SVC(probability=True),
    "Decision Tree": DecisionTreeClassifier(),
    "Logistic Regression": LogisticRegression(max_iter=500),
    "Nearest Neighbour": KNeighborsClassifier(),
}

if HAS_XGBOOST:
    CLASSIFIERS["XGBoost"] = xgb.XGBClassifier(eval_metric="mlogloss", use_label_encoder=False)

FEATURES = [
    "mq6_1","mq135_1","mq137_1",
    "mq6_2","mq135_2","mq137_2",
    "mems_nh3_1","mems_ethanol_1","mems_odor_1",
    "mems_nh3_2","mems_ethanol_2","mems_odor_2",
    "dht_temp","dht_hum"
]

# ================= Train All Classifiers =================
def train_all_with_logs():
    if not os.path.exists(LOG_FILE):
        print("❌ No VOC log file found to train.")
        return

    try:
        tree = ET.parse(LOG_FILE)
        root = tree.getroot()
    except Exception as e:
        print(f"❌ Error reading XML: {e}")
        return

    X, y = [], []
    for entry in root.findall("entry"):
        try:
            features = [float(entry.find(f).text or 0) for f in FEATURES]
            user_id = entry.find("user_id").text
            if user_id:
                X.append(features)
                y.append(user_id)
        except:
            continue

    if not X:
        print("⚠️ No valid VOC data found.")
        return

    X = np.array(X)
    y = np.array(y)
    unique_classes = len(np.unique(y))

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, os.path.join(MODEL_DIR, "VOC_scaler.pkl"))
    print("✅ Feature scaler saved as models/VOC_scaler.pkl\n")

    for clf_name, clf in CLASSIFIERS.items():
        if unique_classes < 2 and clf_name in ["SVM", "Logistic Regression", "XGBoost"]:
            print(f"❌ Skipping {clf_name}: requires ≥2 classes, only {unique_classes} found.")
            continue
        try:
            if clf_name == "XGBoost":
                le = LabelEncoder()
                y_encoded = le.fit_transform(y)
                clf.fit(X_scaled, y_encoded)
                joblib.dump({"model": clf, "label_encoder": le}, os.path.join(MODEL_DIR, "XGBoost_model.pkl"))
            else:
                clf.fit(X_scaled, y)
                joblib.dump(clf, os.path.join(MODEL_DIR, f"{clf_name.replace(' ', '_')}_model.pkl"))
            print(f"✅ {clf_name} model trained for {unique_classes} users.")
        except Exception as e:
            print(f"❌ Training failed for {clf_name}: {e}")

# ================= Train Single Classifier =================
def train(classifier_name):
    if classifier_name not in CLASSIFIERS:
        print(f"❌ Classifier '{classifier_name}' not found.")
        return
    if not os.path.exists(LOG_FILE):
        print("❌ No VOC log file found to train.")
        return

    try:
        tree = ET.parse(LOG_FILE)
        root = tree.getroot()
    except Exception as e:
        print(f"❌ Error reading XML: {e}")
        return

    X, y = [], []
    for entry in root.findall("entry"):
        try:
            features = [float(entry.find(f).text or 0) for f in FEATURES]
            user_id = entry.find("user_id").text
            if user_id:
                X.append(features)
                y.append(user_id)
        except:
            continue

    if not X:
        print("⚠️ No valid VOC data found.")
        return

    X = np.array(X)
    y = np.array(y)
    unique_classes = len(np.unique(y))

    if unique_classes < 2 and classifier_name in ["SVM", "Logistic Regression", "XGBoost"]:
        print(f"❌ Cannot train {classifier_name}: requires ≥2 classes, only {unique_classes} found.")
        return

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, os.path.join(MODEL_DIR, "VOC_scaler.pkl"))

    clf = CLASSIFIERS[classifier_name]
    model_file = os.path.join(MODEL_DIR, f"{classifier_name.replace(' ', '_')}_model.pkl")

    try:
        if classifier_name == "XGBoost":
            le = LabelEncoder()
            y_encoded = le.fit_transform(y)
            clf.fit(X_scaled, y_encoded)
            joblib.dump({"model": clf, "label_encoder": le}, model_file)
        else:
            clf.fit(X_scaled, y)
            joblib.dump(clf, model_file)
        print(f"✅ {classifier_name} model trained and saved as {model_file}")
    except Exception as e:
        print(f"❌ Training failed for {classifier_name}: {e}")

# ================= CLI =================
if __name__ == "__main__":
    train_all_with_logs()
