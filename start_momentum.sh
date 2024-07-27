#!/bin/bash

# Bring up all services except momentum and knowledge_graph
docker-compose up -d

# Wait for postgres to be ready
echo "Waiting for postgres to be ready..."
until docker inspect -f {{.State.Health.Status}} postgres | grep -q "healthy"; do
  sleep 5
done

# Change to knowledge_graph directory
cd knowledge_graph

# Start celery worker and main application
echo "Starting Celery worker..."
celery --app=inferflow worker -l INFO --pool solo -Q ${CELERY_QUEUE_NAME} &

echo "Starting main application..."
python3 main.py &

# Return to the original directory
cd ..

# Run momentum application with migrations
echo "Starting momentum application..."
alembic upgrade head && gunicorn --worker-class uvicorn.workers.UvicornWorker --timeout 1800 --bind 0.0.0.0:8001 --log-level debug server.main:app
