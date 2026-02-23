from cryptography.fernet import Fernet
import os

KEY_FILE = "secret.key"


def _load_or_create_key():
    """
    Load AES key from file or create one if missing.
    """
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        os.chmod(KEY_FILE, 0o600)  # owner read/write only
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return key


# Initialize Fernet cipher once
_cipher = Fernet(_load_or_create_key())


def encrypt_bytes(data: bytes) -> bytes:
    """
    Encrypt raw bytes.
    """
    if not isinstance(data, bytes):
        raise TypeError("encrypt_bytes expects bytes")
    return _cipher.encrypt(data)


def decrypt_bytes(data: bytes) -> bytes:
    """
    Decrypt encrypted bytes.
    """
    if not isinstance(data, bytes):
        raise TypeError("decrypt_bytes expects bytes")
    return _cipher.decrypt(data)
