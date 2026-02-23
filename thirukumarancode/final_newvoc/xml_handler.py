import xml.etree.ElementTree as ET

def save_user_to_xml(user_data):
    tree = ET.parse("users.xml")
    root = tree.getroot()

    user_elem = ET.Element("user")
    for key, value in user_data.items():
        if isinstance(value, list):
            sub_elem = ET.SubElement(user_elem, key)
            for item in value:
                img_elem = ET.SubElement(sub_elem, "image")
                img_elem.text = item
        else:
            sub_elem = ET.SubElement(user_elem, key)
            sub_elem.text = str(value)

    root.append(user_elem)
    tree.write("users.xml")

def load_users_from_xml():
    tree = ET.parse("users.xml")
    root = tree.getroot()
    users = []

    for user_elem in root.findall("user"):
        user_data = {}
        for elem in user_elem:
            if elem.tag == "fingerprints":
                images = [img_elem.text for img_elem in elem.findall("image")]
                user_data[elem.tag] = images
            else:
                user_data[elem.tag] = elem.text
        if "user_id" not in user_data or not user_data["user_id"]:
            import uuid
            user_data["user_id"] = str(uuid.uuid4())[:8]  # generate new if missing

        if "finger_id" not in user_data or not user_data["finger_id"]:
            user_data["finger_id"] = "0"
        users.append(user_data)
    return users

def get_user_by_finger_id(finger_id):
    users = load_users_from_xml()
    for user in users:
        if user.get("finger_id") == str(finger_id):
            return user
    return None

def delete_user_by_name(name):
    tree = ET.parse("users.xml")
    root = tree.getroot()
    finger_id = None

    for user_elem in root.findall("user"):
        name_elem = user_elem.find("name")
        if name_elem is not None and name_elem.text == name:
            fid_elem = user_elem.find("finger_id")
            if fid_elem is not None and fid_elem.text is not None:
                finger_id = int(fid_elem.text)
            root.remove(user_elem)
            break

    tree.write("users.xml")
    return finger_id
