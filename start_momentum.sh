#!/bin/bash

# Bring up all services except momentum
docker-compose up -d

# Wait for postgres and knowledge-graph to be ready
echo "Waiting for postgres and knowledge_graph to be ready..."
until docker inspect -f {{.State.Health.Status}} postgres | grep -q "healthy" && docker inspect -f {{.State.Status}} knowledge_graph | grep -q "running"; do
  sleep 5
done

# Run momentum application with migrations
echo "Starting momentum application..."
alembic upgrade head && gunicorn --worker-class uvicorn.workers.UvicornWorker --timeout 1800 --bind 0.0.0.0:8001 --log-level debug server.main:app
