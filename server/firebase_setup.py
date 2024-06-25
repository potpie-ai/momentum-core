import os

import firebase_admin
from firebase_admin import auth, credentials


def firebase_init():
    cred = credentials.Certificate(
        f"{os.getcwd()}/firebase_service_account.json"
    )
    firebase_admin.initialize_app(cred)
