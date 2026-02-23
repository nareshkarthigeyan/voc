import shutil
import sqlite3
import os

DB_FILE = "voc_biometrics.db"
EXPORT_DIR = "export"
EXPORT_ZIP = "training_bundle.zip"

os.makedirs(EXPORT_DIR, exist_ok=True)

# Copy DB
shutil.copy(DB_FILE, os.path.join(EXPORT_DIR, DB_FILE))

# Zip it
shutil.make_archive("training_bundle", "zip", EXPORT_DIR)

print("Training data exported:", EXPORT_ZIP)
