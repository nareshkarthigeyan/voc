from tools.xml_dataset_loader import load_voc_samples_from_xml
from Features.feature_extractor import extract_features

XML_PATH = "VOC_User_Data/voc_log3.xml"

voc_samples = load_voc_samples_from_xml(XML_PATH)

print(f"Loaded {len(voc_samples)} samples")

features = extract_features(voc_samples)

print("\nExtracted features:")
for k, v in features.items():
    print(f"{k}: {v}")
