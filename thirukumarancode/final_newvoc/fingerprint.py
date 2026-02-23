from pyfingerprint.pyfingerprint import PyFingerprint
import time

class FingerprintSensor:
    def __init__(self, port='/dev/ttyUSB0', baud=57600):
        try:
            self.f = PyFingerprint(port, baud, 0xFFFFFFFF, 0x00000000)
            self.f.verifyPassword()
            print("✅ Fingerprint sensor initialized")
            time.sleep(1)
        except Exception as e:
            print("⚠️ Failed to initialize sensor:", e)
            self.f = None

    def safe_readImage(self):
        for _ in range(20):
            try:
                if self.f.readImage():
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    def safe_convertImage(self, buffer_id):
        for _ in range(5):
            try:
                self.f.convertImage(buffer_id)
                return True
            except Exception as e:
                print(f"⚠️ Retrying convertImage: {e}")
                time.sleep(0.3)
        return False

    def enroll(self, user_name, emp_id):
        if self.f is None:
            return {"status": "failed"}

        try:
            print("🟢 Waiting for finger...")
            if not self.safe_readImage():
                return {"status": "failed"}

            if not self.safe_convertImage(0x01):
                return {"status": "failed"}

            # Check if already enrolled
            result = self.f.searchTemplate()
            if result[0] >= 0:
                print(f"⚠️ Finger already enrolled at position {result[0]}")
                return {"status": "exists", "position": result[0]}

            print("Remove finger...")
            time.sleep(1)
            print("Place the same finger again...")
            if not self.safe_readImage():
                return {"status": "failed"}

            if not self.safe_convertImage(0x02):
                return {"status": "failed"}

            if self.f.compareCharacteristics() == 0:
                print("❌ Fingers do not match")
                return {"status": "failed"}

            position = self.f.storeTemplate()
            print(f"✅ Finger enrolled at position {position}")

            return {"status": "success", "position": position}

        except Exception as e:
            print("⚠️ Enrollment failed:", e)
            return {"status": "failed"}

    def authenticate(self):
        if self.f is None:
            return {"status": "failed"}

        try:
            print("🟢 Waiting for finger for authentication...")
            if not self.safe_readImage():
                return {"status": "failed"}

            if not self.safe_convertImage(0x01):
                return {"status": "failed"}

            position, score = self.f.searchTemplate()
            if position == -1:
                print("❌ No match found")
                return {"status": "failed"}
            else:
                print(f"✅ Match found at position {position} with score {score}")
                return {"status": "authenticated", "finger_id": position}

        except Exception as e:
            print("⚠️ Authentication failed:", e)
            return {"status": "failed"}
