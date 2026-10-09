import base64
import hashlib
import os

from cryptography.fernet import Fernet
from django.conf import settings


def _fernet():
    """Production mein CHANNEL_ENCRYPTION_KEY env set karo (Fernet.generate_key())."""
    key = os.environ.get("CHANNEL_ENCRYPTION_KEY")
    if not key:
        digest = hashlib.sha256(("omnisell-channels:" + settings.SECRET_KEY).encode()).digest()
        key = base64.urlsafe_b64encode(digest)
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt(text: str) -> str:
    return _fernet().encrypt(text.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()
