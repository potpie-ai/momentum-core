import json
import logging
import os

from fastapi import Request
import psycopg2
from psycopg2._json import Json


def get_db_connection():
    return psycopg2.connect(
        os.getenv("POSTGRES_SERVER")
    )


def initialize_db():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        uid VARCHAR(255) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        display_name VARCHAR(255),
        email_verified BOOLEAN DEFAULT FALSE,
        provider_username VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        provider_info JSONB
    );
    """

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(create_table_query)
        conn.commit()
        logging.info("Table 'users' initialized successfully.")
    except Exception as e:
        conn.rollback()
        logging.exception(f"Error initializing table: {e}")
    finally:
        cursor.close()
        conn.close()


def get_user_id_by_firebase_id(firebase_id):
    query = "SELECT id FROM users WHERE firebase_id = %s"


def get_user_id_by_email(email):
    query = "SELECT uid FROM users WHERE email = %s"

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, (email,))
        user_id = cursor.fetchone()
        if user_id:
            return user_id[0]
        else:
            logging.info(f"No user found with email: {email}")
            return None
    except Exception as e:
        logging.exception(f"Error retrieving user ID: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_user_id_by_username(username):
    query = 'SELECT uid, email FROM users WHERE provider_username = %s'

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, (username,))
        user_details = cursor.fetchone()
        if user_details:
            return user_details
        else:
            logging.info(f"No user found with provider username: {username}")
            return None
    except Exception as e:
        logging.exception(f"Error retrieving user ID: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def add_users_to_additional_data(request: Request, user_details):
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
