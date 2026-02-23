import xml.etree.ElementTree as ET
import os
from datetime import datetime

LOG_FILE = "voc_log.xml"

def log_voc(name, user_id, voc_data):
    # Initialize file if it doesn't exist or is empty
    if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
        root = ET.Element("logs")
        tree = ET.ElementTree(root)
        tree.write(LOG_FILE)

    # Parse XML safely
    try:
        tree = ET.parse(LOG_FILE)
        root = tree.getroot()
    except ET.ParseError:
        # File is corrupt, recreate
        root = ET.Element("logs")
        tree = ET.ElementTree(root)

    # Add new entry
    entry = ET.SubElement(root, "entry")
    ET.SubElement(entry, "name").text = name
    ET.SubElement(entry, "user_id").text = str(user_id)
    for k, v in voc_data.items():
        ET.SubElement(entry, k).text = str(v)
    ET.SubElement(entry, "timestamp").text = datetime.now().isoformat()

    tree.write(LOG_FILE)
    print("✅ VOC log saved")
