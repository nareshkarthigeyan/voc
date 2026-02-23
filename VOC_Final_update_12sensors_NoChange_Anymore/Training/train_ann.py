import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import LabelEncoder
from training.load_features import load_training_data
import joblib

# Load data
X, y = load_training_data(
    "features.csv",
    "models/voc_scaler.pkl"
)

# Encode labels
le = LabelEncoder()
y_enc = le.fit_transform(y)
joblib.dump(le, "models/ann_label_encoder.pkl")

# ANN model
model = Sequential([
    Dense(64, activation="relu", input_shape=(X.shape[1],)),
    Dropout(0.3),
    Dense(32, activation="relu"),
    Dense(len(set(y_enc)), activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

es = EarlyStopping(patience=10, restore_best_weights=True)

model.fit(
    X, y_enc,
    epochs=100,
    batch_size=16,
    callbacks=[es],
    verbose=1
)

# Save model
model.save("models/ANN_model.keras")
print("✅ ANN model saved")
