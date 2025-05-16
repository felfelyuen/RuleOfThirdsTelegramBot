import os
import firebase_admin
from firebase_admin import credentials, firestore

def init_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:

        current_dir = os.path.dirname(__file__)
        cert_path = os.path.join(current_dir, "serviceAccountKey.json")

        cred = credentials.Certificate(cert_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()