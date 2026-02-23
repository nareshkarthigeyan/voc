import xml.etree.ElementTree as ET
import os
from datetime import datetime

XML_FILE = "users.xml"


# ---------- INIT ----------
def init_users_xml():
    if not os.path.exists(XML_FILE):
        root = ET.Element("Users")
        tree = ET.ElementTree(root)
        tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)


# ---------- SAVE USER ----------
def save_user_voc(user_id, user_name, feature_vector):
    """
    user_id        : str
    user_name      : str
    feature_vector : dict (Min / Mean / Max features)
    """

    init_users_xml()

    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    user_elem = ET.SubElement(root, "User")
    user_elem.set("id", user_id)
    user_elem.set("registered_at", datetime.now().isoformat())

    name_elem = ET.SubElement(user_elem, "Name")
    name_elem.text = user_name

    features_elem = ET.SubElement(user_elem, "VOC_Features")
    for key, value in feature_vector.items():
        f = ET.SubElement(features_elem, "Feature")
        f.set("name", key)
        f.text = str(value)

    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)


# ---------- LOAD ALL USERS ----------
def load_all_users():
    init_users_xml()

    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    users = []

    for user_elem in root.findall("User"):
        user_data = {
            "user_id": user_elem.get("id"),
            "user_name": user_elem.find("Name").text,
            "features": {}
        }

        features_node = user_elem.find("VOC_Features")
        if features_node is not None:
            for f in features_node.findall("Feature"):
                try:
                    user_data["features"][f.get("name")] = float(f.text)
                except (TypeError, ValueError):
                    user_data["features"][f.get("name")] = 0.0

        users.append(user_data)

    return users


# ---------- GET USER BY ID ----------
def get_user_by_id(user_id):
    users = load_all_users()
    for user in users:
        if user["user_id"] == user_id:
            return user
    return None


# ---------- DELETE USER ----------
def delete_user_by_id(user_id):
    init_users_xml()

    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    for user_elem in root.findall("User"):
        if user_elem.get("id") == user_id:
            root.remove(user_elem)
            tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
            return True

    return False
