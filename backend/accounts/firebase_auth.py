"""Firebase ID token verify. App Google se login karti hai -> Firebase ID token -> yahan check."""
import os

from google.auth.transport import requests as grequests
from google.oauth2 import id_token


class NotConfigured(Exception):
    pass


def verify(token):
    project = os.environ.get("FIREBASE_PROJECT_ID", "").strip()
    if not project:
        raise NotConfigured("FIREBASE_PROJECT_ID set nahi hai.")
    # Signature, expiry, audience (= project id) aur issuer sab check hota hai. Galat par ValueError.
    return id_token.verify_firebase_token(token, grequests.Request(), audience=project)
