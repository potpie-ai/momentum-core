import os
import firebase_admin
from firebase_admin import auth, credentials
import base64
import json
import logging

def firebase_init():
    service_account_base64 = os.getenv('FIREBASE_SERVICE_ACCOUNT')
    cred = None
    
    if service_account_base64:
        try:
            service_account_info = base64.b64decode(service_account_base64).decode('utf-8')
            service_account_json = json.loads(service_account_info)
            cred = credentials.Certificate(service_account_json)
            logging.info("Loaded Firebase credentials from environment variable.")
        except Exception as e:
            logging.error(f"Error decoding Firebase service account from environment variable: {e}")
    
    if not cred:
        try:
            cred = credentials.Certificate(f"{os.getcwd()}/firebase_service_account.json")
            logging.info("Loaded Firebase credentials from local file as fallback.")
        except Exception as e:
            logging.error(f"Error loading Firebase service account from local file: {e}")
            return  # Exit the function if credentials cannot be loaded

    firebase_admin.initialize_app(cred)