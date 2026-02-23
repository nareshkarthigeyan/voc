import xml.etree.ElementTree as ET
import os
from datetime import datetime
from utils.aes_secure import encrypt_bytes, decrypt_bytes

XML_FILE = "voc_log_encrypted.xml"


def load_tree_decrypted():
    if not os.path.exists(XML_FILE):
        return ET.Element("logs")

    with open(XML_FILE, "rb") as f:
        encrypted_data = f.read()

    decrypted = decrypt_bytes(encrypted_data)
    return ET.fromstring(decrypted)


def save_tree_encrypted(root):
    xml_data = ET.tostring(root, encoding="utf-8")
    encrypted = encrypt_bytes(xml_data)

    tmp = XML_FILE + ".tmp"
    with open(tmp, "wb") as f:
        f.write(encrypted)

    os.replace(tmp, XML_FILE)


def log_voc(mode: str, user_id: str, user_name: str, samples: list):
    """
    mode      : REGISTRATION | VERIFICATION
    user_id   : unique user identifier
    user_name : user display name
    samples   : list of VOC readings (dicts)
    """

    if mode not in ("REGISTRATION", "VERIFICATION"):
        raise ValueError("Invalid mode for VOC logging")

    root = load_tree_decrypted()

    for sample in samples:
        entry = ET.SubElement(root, "entry")

        ET.SubElement(entry, "mode").text = mode
        ET.SubElement(entry, "user_id").text = user_id
        ET.SubElement(entry, "user_name").text = user_name
        ET.SubElement(entry, "timestamp").text = datetime.now().isoformat()

        for k, v in sample.items():
            ET.SubElement(entry, k).text = str(v)

    save_tree_encrypted(root)
