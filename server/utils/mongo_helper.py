# utils.py
import os
import certifi
from mongoengine import connect, connection

def get_mongo_connection():
    db_name = os.getenv("MONGO_DB_NAME", "test")
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    env = os.getenv("ENV", "development")  # Assume development if ENV is not set

    if env == "production":
        connect(db_name, host=mongo_uri, tlsCAFile=certifi.where())
    else:
        connect(db_name, host=mongo_uri)
    
    return connection.get_connection()

