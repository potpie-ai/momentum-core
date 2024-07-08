import os
from fastapi import Request
from sqlalchemy.orm import Session
from server.db.session import SessionManager
from server.crud import crud_utils

def get_db() -> Session:
    with SessionManager() as db:
        yield db


def get_user_id_by_email(email: str):
    with SessionManager() as db:
        user = crud_utils.get_user_by_email(db, email)
        if user:
            return user.uid
        else:
            print(f"No user found with email: {email}")
            return None

def get_user_id_by_username(username: str):
    with SessionManager() as db:
        user = crud_utils.get_user_by_username(db, username)
        if user:
            return user.uid, user.email
        else:
            print(f"No user found with provider username: {username}")
            return None

def add_users_to_additional_data(request: Request, user_details: dict):
    user_state_value = {
        "user_id": user_details["uid"],
        "email": user_details["email"]
    }
    request.state.user = user_state_value
    request.state.additional_data = {
        "uid": user_details['uid'],
        "display_name": user_details.get('displayName'),
        "email_verified": user_details.get('emailVerified', False),
        "created_at": user_details['createdAt'],
        "provider_data": user_details.get('providerData')
    }
