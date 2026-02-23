from pyfingerprint.pyfingerprint import PyFingerprint

try:
    f = PyFingerprint('/dev/ttyAMA0', 57600, 0xFFFFFFFF, 0x00000000)

    if not f.verifyPassword():
        raise ValueError("Fingerprint sensor password is wrong!")

    template_count = f.getTemplateCount()
    print(f"Found {template_count} templates.")

    for page in range(template_count):
        if f.deleteTemplate(page):
            print(f"✅ Deleted template at position #{page}")

    print("✅ All templates cleared.")

except Exception as e:
    print("⚠️ Operation failed:", e)
