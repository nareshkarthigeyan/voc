"""Mock Logger for VOC data."""
import json
from datetime import datetime


def log_voc(mode, user_name, user_id, samples):
    """
    Log VOC sensor data to file.
    
    Args:
        mode: "REGISTRATION" or "VERIFICATION"
        user_name: Name of the user
        user_id: User ID
        samples: List of sensor samples
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "user_name": user_name,
        "user_id": user_id,
        "num_samples": len(samples),
        "samples": samples[:5]  # Only log first 5 samples to save space
    }
    
    print(f"Logger: {mode} - {user_name} ({user_id}) - {len(samples)} samples")
    
    # Optionally write to file
    try:
        with open("voc_log.json", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Logger warning: Could not write to file - {e}")
