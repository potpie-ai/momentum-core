from celery import Celery
import os
import redis

# Replace with your Redis instance IP and port
REDISHOST = os.getenv("REDISHOST")
REDISPORT = int(os.getenv("REDISPORT", 6379))

# Initialize the Redis client
redis_client = redis.StrictRedis(host=REDISHOST, port=REDISPORT)

# Function to convert Redis client to URL
def redis_client_to_url(client):
    connection_pool = client.connection_pool
    return f'redis://{connection_pool.connection_kwargs["host"]}:{connection_pool.connection_kwargs["port"]}/0'

# Generate the Redis URL from the client
REDIS_URL = redis_client_to_url(redis_client)

celery_worker = Celery('KnowledgeGraph', broker=REDIS_URL, backend=REDIS_URL)