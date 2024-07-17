from celery import Celery
import os

# Retrieve Redis connection details from environment variables
REDISHOST = os.getenv("REDISHOST", "localhost")
REDISPORT = int(os.getenv("REDISPORT", 6379))
REDISUSER = os.getenv("REDISUSER", "")
REDISPASSWORD = os.getenv("REDISPASSWORD", "")
QUEUE_NAME = os.getenv("CELERY_QUEUE_NAME", "staging")


# Construct the Redis URL including the username and password
if REDISUSER and REDISPASSWORD:
    REDIS_URL = f'redis://{REDISUSER}:{REDISPASSWORD}@{REDISHOST}:{REDISPORT}/0'
else:
    REDIS_URL = f'redis://{REDISHOST}:{REDISPORT}/0'

# Initialize the Celery worker
celery_worker = Celery('KnowledgeGraph', broker=REDIS_URL, backend=REDIS_URL)

celery_worker.conf.task_routes = {
        "knowledgegraph.task.infer_flows": {'queue': QUEUE_NAME}
}