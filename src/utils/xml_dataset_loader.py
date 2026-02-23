import xml.etree.ElementTree as ET

IGNORE_TAGS = {
    "name",
    "hand",
    "location",
    "category",
    "timestamp"
}

def load_voc_samples_grouped_by_user(xml_file):
    """
    Returns:
    {
        user_id_1: [sample_dict, sample_dict, ...],
        user_id_2: [sample_dict, sample_dict, ...],
        ...
    }
    """

    tree = ET.parse(xml_file)
    root = tree.getroot()

    user_samples = {}

    for entry in root.findall("entry"):
        user_id_elem = entry.find("user_id")
        if user_id_elem is None or not user_id_elem.text:
            continue

        user_id = user_id_elem.text.strip()

        sample = {}
        for elem in entry:
            if elem.tag in IGNORE_TAGS or elem.tag == "user_id":
                continue

            try:
                sample[elem.tag] = float(elem.text)
            except (TypeError, ValueError):
                sample[elem.tag] = 0.0

        if not sample:
            continue

        user_samples.setdefault(user_id, []).append(sample)

    return user_samples
