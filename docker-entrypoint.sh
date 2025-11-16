#!/bin/bash
set -e

echo "================================"
echo "Starting deployment migrations..."
echo "================================"

# Ensure DATA directory exists
mkdir -p /data
echo "✓ Data directory ready: /data"

# Run all migrations in order
echo ""
echo "Running migration 1/3: add_video_job_fields"
/app/.venv/bin/python /app/backend/migrations/add_video_job_fields.py

echo ""
echo "Running migration 2/3: add_clients_campaigns"
/app/.venv/bin/python /app/backend/migrations/add_clients_campaigns.py

echo ""
echo "Running migration 3/3: consolidate_assets_table"
/app/.venv/bin/python /app/backend/migrations/consolidate_assets_table.py

echo ""
echo "================================"
echo "All migrations completed!"
echo "================================"
echo ""

# Start the application
echo "Starting uvicorn server..."
exec /app/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8080}"
