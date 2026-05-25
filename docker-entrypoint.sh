#!/bin/sh

set -e

echo "⏳ Waiting for database to be ready..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  sleep 1
done
echo "✅ Database is ready!"

echo "🔄 Running Alembic migrations..."
alembic upgrade head
echo "✅ Migrations applied!"

echo "🚀 Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload