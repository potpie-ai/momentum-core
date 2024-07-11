from firebase_admin import firestore, App
from functools import wraps
from typing import Optional, List


class FirestoreHelper:
    def __init__(self):
        self.client = firestore.client()

    def get(self, doc_id: str, collection: Optional[str] = ""):
        return self.client.collection(collection).document(doc_id)

    def put(self, collection: str, doc_id: str, payload: dict):
        self.client.collection(collection).document(doc_id).set(payload)

    def patch(self, collection: str, doc_id: str, payload: dict):
        doc_ref = self.client.collection(collection).document(doc_id)
        if not doc_ref.get().exists:
            doc_ref.set(payload)
        else:
            doc_ref.update(payload)

    def delete(self, collection: str, doc_id: str):
        self.client.collection(collection).document(doc_id).delete()

    def delete_key(self, collection: str, doc_id: str, key: str):
        doc_ref = self.client.collection(collection).document(doc_id)
        update_data = {f"{key}": firestore.DELETE_FIELD}

        doc_ref.update(update_data)
        