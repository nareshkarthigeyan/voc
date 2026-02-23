import numpy as np
from scipy.stats import skew, kurtosis


def safe_float(value):
    """Ensure no NaN or inf values ever enter model"""
    try:
        if value is None or not np.isfinite(value):
            return 0.0
        return float(value)
    except:
        return 0.0


def extract_features(voc_samples):
    """
    Robust statistical feature extraction.

    Features per sensor:
    - min
    - mean
    - max
    - std
    - median
    - iqr
    - skew
    - kurtosis
    - cv (coefficient of variation)
    - energy
    """

    if not voc_samples:
        raise ValueError("voc_samples list is empty")

    features = {}

    # Collect all sensor names from first sample
    sensor_keys = voc_samples[0].keys()

    for sensor in sensor_keys:

        # Collect ALL values (including zero) for stability
        values = [
            safe_float(sample.get(sensor, 0.0))
            for sample in voc_samples
        ]

        values_np = np.array(values, dtype=float)

        # If all values are zero, avoid division problems
        if np.all(values_np == 0):
            min_v = max_v = mean_v = std_v = median_v = 0.0
            iqr_v = skew_v = kurt_v = cv_v = energy_v = 0.0
        else:
            min_v = safe_float(np.min(values_np))
            max_v = safe_float(np.max(values_np))
            mean_v = safe_float(np.mean(values_np))
            std_v = safe_float(np.std(values_np))
            median_v = safe_float(np.median(values_np))

            # IQR
            q75, q25 = np.percentile(values_np, [75, 25])
            iqr_v = safe_float(q75 - q25)

            # Skew
            if len(values_np) >= 3:
                skew_v = safe_float(skew(values_np, bias=False))
            else:
                skew_v = 0.0

            # Kurtosis
            if len(values_np) >= 4:
                kurt_v = safe_float(kurtosis(values_np, fisher=True, bias=False))
            else:
                kurt_v = 0.0

            # Coefficient of Variation
            if mean_v != 0:
                cv_v = safe_float(std_v / mean_v)
            else:
                cv_v = 0.0

            # Energy
            energy_v = safe_float(np.sum(values_np ** 2))

        # Store features
        features[f"{sensor}_min"] = min_v
        features[f"{sensor}_mean"] = mean_v
        features[f"{sensor}_max"] = max_v
        features[f"{sensor}_std"] = std_v
        features[f"{sensor}_median"] = median_v
        features[f"{sensor}_iqr"] = iqr_v
        features[f"{sensor}_skew"] = skew_v
        features[f"{sensor}_kurtosis"] = kurt_v
        features[f"{sensor}_cv"] = cv_v
        features[f"{sensor}_energy"] = energy_v

    return features
