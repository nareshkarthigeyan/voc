import xml.etree.ElementTree as ET


def parse_sensor_xml(xml_path):
    """
    Reads a raw VOC XML file and returns:
    voc_data : dict  (sensor_id -> value)
    env_data : dict  (environment metadata)
    """

    tree = ET.parse(xml_path)
    root = tree.getroot()

    voc_data = {}
    env_data = {}

    # ---- VOC Sensors ----
    voc_node = root.find("VOC_Sensors")
    if voc_node is not None:
        for sensor in voc_node.findall("Sensor"):
            sensor_id = sensor.get("id")
            try:
                voc_data[sensor_id] = float(sensor.text)
            except (TypeError, ValueError):
                voc_data[sensor_id] = 0.0

    # ---- Environment ----
    env_node = root.find("Environment")
    if env_node is not None:
        for elem in env_node:
            try:
                env_data[elem.tag] = float(elem.text)
            except (TypeError, ValueError):
                env_data[elem.tag] = 0.0

    return voc_data, env_data
