#!/bin/bash

# Start nginx in background
nginx

# Start Flask backend
cd /app/backend
export PORT=8081
gunicorn --bind 0.0.0.0:8081 --workers 4 --timeout 120 run:app

