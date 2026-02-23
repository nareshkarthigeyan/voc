from cryptography.fernet import Fernet

# ---- Paths ----
KEY_FILE = "/home/voc/Desktop/VOC_updated/secret.key"          # same key used during encryption
ENCRYPTED_XML = "/home/voc/Desktop/VOC_updated/voc_log_encrypted.xml"
OUTPUT_XML = "/home/voc/Desktop/VOC_updated/voc_log_Dencrypted.xml"

# ---- Load key ----
with open(KEY_FILE, "rb") as f:
    key = f.read()

cipher = Fernet(key)

# ---- Decrypt ----
with open(ENCRYPTED_XML, "rb") as f:
    encrypted_data = f.read()

decrypted_data = cipher.decrypt(encrypted_data)

# ---- Save decrypted XML ----
with open(OUTPUT_XML, "wb") as f:
    f.write(decrypted_data)

print("✅ XML decrypted successfully")
