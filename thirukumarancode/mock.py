# mock_hardware.py
import random
import os

class FingerprintSensor:
    def authenticate(self):
        # Simulate random authentication success/failure
        if random.choice([True, False]):
            return {"status": "authenticated", "finger_id": random.randint(1, 10)}
        return {"status": "failed", "finger_id": None}

    def enroll(self, name, emp_id):
        # Simulate enrolling a fingerprint
        fake_image = "fingerprint_mock.png"
        # create a dummy image file if not already
        if not os.path.exists(fake_image):
            from PIL import Image
            img = Image.new("RGB", (100, 100), "gray")
            img.save(fake_image)
        return {"status": "success", "position": random.randint(1, 10), "image_path": fake_image}

class VOCSensor:
    def read(self):
        # Return fake VOC sensor values
        return [random.uniform(0, 1) for _ in range(5)]
