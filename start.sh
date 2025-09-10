#!/bin/bash

# Use Railway's PORT if available, otherwise default to 8003
PORT=${PORT:-8003}

echo "Starting application on port $PORT"

# Start gunicorn with the resolved port
exec gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 app:app

