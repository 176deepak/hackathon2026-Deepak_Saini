#!/bin/sh
set -e

echo "Running Alembic migrations..."
alembic upgrade head

python -m scripts.seed_data

echo "Starting app....."
exec python main.py