import os
import json
import secrets
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from .config import KDF_ITERS, NONCE_LEN, SALT_SIZE
from . import models

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERS,
        backend=default_backend()
    )
    return kdf.derive(password.encode('utf-8'))

def encrypt_payload(key: bytes, payload: dict):
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_LEN)
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    ct = aesgcm.encrypt(nonce, data, None)
    return nonce, ct

def decrypt_payload(key: bytes, nonce: bytes, ct: bytes):
    aesgcm = AESGCM(key)
    data = aesgcm.decrypt(nonce, ct, None)
    return json.loads(data.decode('utf-8'))

def make_password_verifier(password: str, salt: bytes) -> bytes:
    return derive_key(password, salt)

def verify_password(password: str, salt: bytes, verifier: bytes) -> bool:
    try:
        candidate = derive_key(password, salt)
        return secrets.compare_digest(candidate, verifier)
    except Exception:
        return False

# --- Helpers ---
def mask_card_number(num: str):
    n = ''.join(ch for ch in num if ch.isdigit())
    if len(n) <= 4: return '*' * max(1, len(n))
    return ('*' * (len(n)-4)) + n[-4:]

# def user_key_from_user(user: models.User) -> bytes:
#     # WARNING: Simplification. See original notes.
#     return derive_key(user.password_verifier.hex(), user.password_salt)