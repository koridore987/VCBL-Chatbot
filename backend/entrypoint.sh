#!/bin/bash

set -e

# Ensure script is executable and has proper line endings
# This helps with cross-platform compatibility

# Ensure we are in backend directory
cd /app/backend

# Export Flask app module for CLI
export FLASK_APP=run.py

echo "Running database migrations (flask db upgrade)..."
python -m flask db upgrade

# Optionally initialize Super Admin on first setup
# Set INIT_ADMIN_ON_START=true to enable (idempotent; skips if super exists)
if [ "${INIT_ADMIN_ON_START}" = "true" ]; then
  echo "Initializing super admin account (flask init-admin)..."
  python -m flask init-admin || true
fi

echo "Starting Supervisor (nginx + gunicorn)"
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf