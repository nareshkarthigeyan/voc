import xml.etree.ElementTree as ET
import os
import tempfile
from datetime import datetime
from aes_secure import encrypt_bytes, decrypt_bytes

XML_FILE = "user_voc_data_encrypted.xml"


# ---------- Atomic write ----------
def _atomic_write(data: bytes, path: str):
    dir_name = os.path.dirname(path) or "."
    with tempfile.NamedTemporaryFile(dir=dir_name, delete=False) as tmp:
        tmp.write(data)
        temp_name = tmp.name
    os.replace(temp_name, path)


# ---------- Load / Save ----------
def load_tree_decrypted() -> ET.Element:
    if not os.path.exists(XML_FILE):
        return ET.Element("logs")

    with open(XML_FILE, "rb") as f:
        encrypted_data = f.read()

    decrypted = decrypt_bytes(encrypted_data)
    return ET.fromstring(decrypted)


def save_tree_encrypted(root: ET.Element):
    xml_data = ET.tostring(root, encoding="utf-8")
    encrypted = encrypt_bytes(xml_data)
    _atomic_write(encrypted, XML_FILE)


# ---------- Recursive dict → XML ----------
def _dict_to_xml(parent: ET.Element, data: dict):
    for key, value in data.items():
        child = ET.SubElement(parent, key)

        if isinstance(value, dict):
            _dict_to_xml(child, value)

        elif isinstance(value, list):
            for item in value:
                item_elem = ET.SubElement(child, "item")
                item_elem.text = str(item)

        else:
            child.text = str(value)


# ---------- Public API ----------
def log_user_data(user_id: str, user_name: str, data: dict):
    """
    Stores ANY biometric / sensor data dynamically.
    fingerprint, voc, face, etc. are all optional.
    """

    root = load_tree_decrypted()

    entry = ET.SubElement(root, "entry")
    ET.SubElement(entry, "user_id").text = user_id
    ET.SubElement(entry, "user_name").text = user_name
    ET.SubElement(entry, "timestamp").text = datetime.now().isoformat()

    _dict_to_xml(entry, data)

    save_tree_encrypted(root)
