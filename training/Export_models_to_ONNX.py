import joblib
import json
import numpy as np
from pathlib import Path

from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

MODELS_DIR = Path("models/trained_models")
ONNX_DIR = Path("trained_models_ONNX")

FEATURE_COUNT = None  # will be loaded

def main():
    global FEATURE_COUNT

    ONNX_DIR.mkdir(exist_ok=True)

    with open(ONNX_DIR / "metadata.json") as f:
        meta = json.load(f)
        FEATURE_COUNT = meta["feature_count"]

    initial_type = [("input", FloatTensorType([None, FEATURE_COUNT]))]

    models = {
        "rf": "rf_model.pkl",
        "extratrees": "et_model.pkl",
        "svm": "svm_model.pkl",
        "knn": "knn_model.pkl",
        "ann": "ann_model.pkl",
    }

    exported = []

    for name, file in models.items():
        print(f"[INFO] Converting {name}...")
        model = joblib.load(MODELS_DIR / file)

        onnx_model = convert_sklearn(
            model,
            initial_types=initial_type
        )

        with open(ONNX_DIR / f"{name}.onnx", "wb") as f:
            f.write(onnx_model.SerializeToString())

        exported.append(name)

    print("\n✅ ONNX export completed")
    print("Models:", exported)

if __name__ == "__main__":
    main()
