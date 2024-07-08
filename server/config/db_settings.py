import os

from dotenv import load_dotenv
from loguru import logger


class DBSettings:
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    def __init__(self) -> None:
        load_dotenv()
        self.POSTGRES_SERVER = os.getenv("POSTGRES_SERVER")
        self.POSTGRES_USER = os.getenv("POSTGRES_USER")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
        self.POSTGRES_DB = os.getenv("POSTGRES_DB")

        logger.success("Database settings loaded successfully!")


db_settings = DBSettings()

if __name__ == "__main__":
    logger.info(db_settings.POSTGRES_SERVER)
    logger.info(db_settings.POSTGRES_USER)
    logger.info(db_settings.POSTGRES_PASSWORD)
    logger.info(db_settings.POSTGRES_DB)
