from sqlalchemy import create_engine, engine
from sqlalchemy.orm import sessionmaker

from server.config.db_settings import db_settings

engine = create_engine(db_settings.POSTGRES_SERVER, pool_pre_ping=True)
engine = create_engine(
    db_settings.POSTGRES_SERVER,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class SessionManager:
    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
