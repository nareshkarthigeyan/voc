import os
import sys
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, VotingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix
from xgboost import XGBClassifier


def train_ensemble(csv_path, sensor_mode):
    print(f"[LOG] Training cycle initiated for SENSOR_MODE: {sensor_mode}")
    print(f"[LOG] Loading dataset from: {csv_path}")

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[ERROR] Failed to read CSV: {e}")
        return

    if df.empty:
        print("[ERROR] Dataset is empty.")
        return

    print(f"[LOG] Dataset shape: {df.shape}")
    print(f"[LOG] Class distribution:\n{df['user_id'].value_counts()}")

    y = df["user_id"]
    X = df.drop(columns=["user_id", "round_no"])

    feature_order = list(X.columns)
    print(f"[LOG] Features: {len(feature_order)}")

    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    n_classes = len(le.classes_)
    print(f"[LOG] Classes ({n_classes}): {list(le.classes_)}")

    # ── Sanity check: need enough samples per class for CV ──────────────────
    min_samples = y.value_counts().min()
    n_splits = min(5, min_samples)
    if n_splits < 2:
        print("[WARN] Too few samples per class for cross-validation. Need more data.")
        return

    # ── Train / test split (stratified) ─────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, stratify=y_enc, random_state=42
    )
    print(f"[LOG] Train size: {X_train.shape[0]}, Test size: {X_test.shape[0]}")

    output_dir = os.path.join("models", f"{sensor_mode}_sensors")
    os.makedirs(output_dir, exist_ok=True)

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    # ── Model definitions ────────────────────────────────────────────────────
    # Note: ANN wrapped in Pipeline with its own scaler so it's self-contained
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    models_to_train = {
        "rf_model": RandomForestClassifier(
            n_estimators=300,
            max_depth=None,          # let it grow fully — pruning via min_samples
            min_samples_leaf=2,
            class_weight="balanced",
            n_jobs=-1,
            random_state=42
        ),
        "et_model": ExtraTreesClassifier(
            n_estimators=300,
            min_samples_leaf=2,
            class_weight="balanced",
            n_jobs=-1,
            random_state=42
        ),
        "dt_model": DecisionTreeClassifier(
            max_depth=None,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=42
        ),
        "xgb_model": XGBClassifier(
            n_estimators=300,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="mlogloss",
            num_class=n_classes if n_classes > 2 else None,
            n_jobs=-1,
            random_state=42
        ),
        "ann_model": MLPClassifier(
            hidden_layer_sizes=(512, 256, 128),
            max_iter=500,
            learning_rate="adaptive",
            learning_rate_init=0.001,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=20,
            random_state=42
        ),
    }

    results = {}

    for name, model in models_to_train.items():
        print(f"\n[TRAIN] {name}")

        is_ann = name == "ann_model"
        X_tr = X_train_scaled if is_ann else X_train
        X_te = X_test_scaled if is_ann else X_test

        # Cross-validation on training set
        cv_scores = cross_val_score(
            model, X_tr, y_train,
            cv=skf, scoring="accuracy", n_jobs=-1
        )
        print(f"  CV Accuracy:  {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

        # Fit on full train split, evaluate on held-out test
        model.fit(X_tr, y_train)
        train_acc = model.score(X_tr, y_train)
        test_acc = model.score(X_te, y_test)
        print(f"  Train Acc:    {train_acc:.4f}")
        print(f"  Test Acc:     {test_acc:.4f}")

        if train_acc - test_acc > 0.15:
            print(f"  [WARN] Large gap ({train_acc - test_acc:.2f}) — model may be overfitting.")

        y_pred = model.predict(X_te)
        print(f"  Classification Report:\n"
              f"{classification_report(y_test, y_pred, target_names=[str(c) for c in le.classes_])}")

        results[name] = {"cv_mean": cv_scores.mean(), "test_acc": test_acc}

        export_path = os.path.join(output_dir, f"{name}.pkl")
        joblib.dump(model, export_path)
        print(f"  Saved → {export_path}")

    # ── Save shared artifacts ────────────────────────────────────────────────
    joblib.dump(scaler, os.path.join(output_dir, "ann_scaler.pkl"))
    joblib.dump(le, os.path.join(output_dir, "label_encoder.pkl"))
    joblib.dump(feature_order, os.path.join(output_dir, "feature_order.pkl"))

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n[SUMMARY]")
    for name, r in results.items():
        print(f"  {name:15s}  CV={r['cv_mean']:.4f}  Test={r['test_acc']:.4f}")

    best = max(results, key=lambda k: results[k]["test_acc"])
    print(f"\n[BEST MODEL] {best} with Test Accuracy: {results[best]['test_acc']:.4f}")
    print(f"[SUCCESS] Training complete → {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python train_all.py <sensor_mode>")
        sys.exit(1)

    mode = sys.argv[1]
    csv_file = os.path.join(os.path.dirname(__file__), "training_data.csv")
    train_ensemble(csv_file, mode)