#!/bin/bash
set -e

# Use the port assigned by Railway, or default to 8000
PORT=${PORT:-8000}

# Run migrations (optional, but good practice)
echo "Running migrations..."
alembic upgrade head

echo "Starting Uvicorn on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
