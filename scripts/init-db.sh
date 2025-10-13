#!/bin/bash

echo "Initializing database..."

# Wait for database to be ready
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "Database is ready!"

# Run migrations
cd /app/backend
flask db upgrade

echo "Database initialized successfully!"

