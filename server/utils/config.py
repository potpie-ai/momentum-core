from dotenv import load_dotenv
import os

load_dotenv()

neo4j_config = {
    "uri": os.getenv("NEO4J_URI"),
    "username": os.getenv("NEO4J_USERNAME"),
    "password": os.getenv("NEO4J_PASSWORD"),
    "max_connection_lifetime" : int(os.getenv('NEO4J_MAX_CONNECTION_LIFETIME', 1000)),
    "max_connection_pool_size" :int(os.getenv('NEO4J_MAX_CONNECTION_POOL_SIZE', 2))           
}
