import os
from datetime import datetime
from PIL import Image

try:
    from pyfingerprint.pyfingerprint import PyFingerprint
except ImportError:
    print("pyfingerprint library not found. Install using: pip install pyfingerprint")

class FingerprintSensor:
    def __init__(self):
        try:
            #sensor = PyFingerprint('COM3', 57600, 0xFFFFFFFF, 0x00000000)
            self.f = PyFingerprint('/dev/serial0', 57600, 0xFFFFFFFF, 0x00000000)
            if not self.f.verifyPassword():
                raise ValueError('Fingerprint sensor password is wrong!')
            print('Fingerprint sensor initialized.')
        except Exception as e:
            print('Failed to initialize fingerprint sensor:', e)
            self.f = None

    def enroll(self, user_name, emp_id):
        if self.f is None:
            print("Sensor not initialized.")
            return {"status": "failed"}

        try:
            print('Waiting for finger...')
            while self.f.readImage() is False:
                pass

            self.f.convertImage(0x01)
            result = self.f.searchTemplate()
            positionNumber = result[0]

            self.f.createTemplate()
            new_positionNumber = self.f.storeTemplate()

            image_dir = "finger_images"
            os.makedirs(image_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            bmp_path = os.path.join(image_dir, f"{user_name}_{emp_id}_{timestamp}.bmp")
            png_path = bmp_path.replace(".bmp", ".png")

            # Download BMP
            self.f.downloadImage(bmp_path)
            print(f"Fingerprint BMP image saved at {bmp_path}")

            # Convert BMP to proper PNG (so Tkinter and PIL can display)
            img = Image.open(bmp_path).convert("L")
            img.save(png_path)
            print(f"Fingerprint PNG image saved at {png_path}")

            return {
                "status": "success",
                "position": new_positionNumber,
                "image_path": png_path  # Always use PNG for GUI display
            }

        except Exception as e:
            print("Enrollment failed:", e)
            return {"status": "failed"}

    def authenticate(self):
        if self.f is None:
            return {"status": "failed"}

        try:
            print('Waiting for finger for authentication...')
            while self.f.readImage() is False:
                pass

            self.f.convertImage(0x01)
            result = self.f.searchTemplate()
            positionNumber = result[0]

            if positionNumber == -1:
                print("No match found.")
                return {"status": "failed"}
            else:
                print("Match found at position #", positionNumber)
                return {"status": "authenticated", "finger_id": positionNumber}

        except Exception as e:
            print("Authentication failed:", e)
            return {"status": "failed"}
