import base64
from app.core.config import settings

def _xor_cipher(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def encrypt_value(value: str) -> str:
    if not value:
        return ""
    try:
        key_bytes = settings.SECRET_KEY.encode('utf-8')
        raw_bytes = value.encode('utf-8')
        cipher_bytes = _xor_cipher(raw_bytes, key_bytes)
        return "enc:" + base64.b64encode(cipher_bytes).decode('utf-8')
    except Exception:
        return value

def decrypt_value(token: str) -> str:
    if not token:
        return ""
    if not token.startswith("enc:"):
        return token
    try:
        key_bytes = settings.SECRET_KEY.encode('utf-8')
        cipher_bytes = base64.b64decode(token[4:].encode('utf-8'))
        raw_bytes = _xor_cipher(cipher_bytes, key_bytes)
        return raw_bytes.decode('utf-8')
    except Exception:
        return token
