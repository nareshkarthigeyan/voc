# VOC Biometric Intelligence System

An advanced multimodal biometric platform using Volatile Organic Compound (VOC) fingerprinting and optional fingerprint scanning.

## 📁 System Architecture
- **src/app.py**: Main GUI application (CustomTkinter Dark Theme).
- **src/sensors/**: Hardware drivers (VOC sensors, Fan, Hand detection, Fingerprint).
- **src/core/**: Intelligence layer (Feature extraction, Verification, Model logic).
- **src/database/**: Persistence layer (SQLite, Logging).
- **src/utils/**: Analytics and Workflow automation.
- **data/**: Storage for biometric databases and radar profiles.
- **models/**: Trained ensemble models (RF, ET, DT, XGB, ANN).

## 🚀 Getting Started

### 1. Hardware Initialization
Ensure your Raspberry Pi is connected to the sensor array and I2C is enabled.
```bash
# Configure sensor mode (6 or 12)
export VOC_SENSOR_MODE=12
./run.sh
```

### 2. User Enrollment (Phase 1)
- Launch the application and select **NEW USER REGISTRATION**.
- If in 12-sensor mode, you will be prompted for a physical fingerprint scan.
- Follow the prompts to capture 10 rounds of VOC data.
- The system will generate a **Radar Profile** and package your data in `data_exports/`.

### 3. Automated Training (Phase 2)
Transfer your registration ZIP to your training machine and run:
```bash
./train.sh --sensors 12
```
This updates the ensemble models with the latest biometric signatures.

### 4. Identity verification (Phase 3)
- Select **IDENTITY VERIFICATION** in the GUI.
- The system performs multi-factor comparison:
  1. Electronic Nose (VOC Fingerprint)
  2. Neural Network Probability Fusion
  3. Radar Profile Similarity Scoring
- Results include a live **Analytics Dashboard** with Radar and Scatter plots.

## 🛠️ Security & Privacy
- **AES-256 Encryption**: Biometric logs are stored in an encrypted XML format.
- **Local SQLite**: User identity data never leaves the device.
- **Reinforcement Loop**: Use the "Flag Incorrect" feature to train the model on missed detections.

---
*Developed for advanced agentic coding research.*
