from tools.xml_dataset_loader import load_voc_samples_grouped_by_user
from core.feature_extractor import extract_features
from database.user_dao import insert_user
from database.feature_dao import insert_features

# ---------- CONFIG ----------
XML_PATH = "VOC_User_Data/voc_log3.xml"

DATASET_USER_ID = "DATASET_001"
DATASET_USER_NAME = "VOC_XML_DATASET"


def main():
    print("[INFO] Loading VOC samples grouped by user...")
    user_samples = load_voc_samples_grouped_by_user(XML_PATH)

    if not user_samples:
        print("[ERROR] No user data found in XML.")
        return

    print(f"[INFO] Found {len(user_samples)} users in dataset")

    for user_id, samples in user_samples.items():
        print(f"\n[INFO] Processing user {user_id}")
        print(f"Samples: {len(samples)}")

        features = extract_features(samples)

        insert_user(user_id, f"XML_USER_{user_id}")
        insert_features(user_id, features)

        print(f"Stored {len(features)} features")

    print("\n✅ All users imported successfully")


if __name__ == "__main__":
    main()





