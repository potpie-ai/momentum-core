# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port that the app runs on
EXPOSE 8001

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Health check to verify the application is running
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Command to run the application with migrations
CMD ["sh", "-c", "alembic upgrade head && gunicorn --worker-class uvicorn.workers.UvicornWorker --timeout 1800 --bind 0.0.0.0:8001 --log-level debug server.main:app"]