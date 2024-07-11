from celery import Celery
import os

BROKER_URL = os.getenv("REDIS_BROKER_URL")
celery_worker = Celery('KnowledgeGraph', broker=BROKER_URL,  backend=BROKER_URL)