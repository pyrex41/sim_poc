#!/bin/bash
set -e

# Ensure DATA directory exists
mkdir -p /data
echo "✓ Data directory ready: /data"

# Run migrations if RUN_MIGRATIONS is set (default: skip)
# To enable migrations on deployment, set: fly secrets set RUN_MIGRATIONS=true
if [ "${RUN_MIGRATIONS}" = "true" ]; then
    echo ""
    echo "================================"
    echo "Running database migrations..."
    echo "================================"

    # Auto-discover and run all migration scripts in backend/migrations/
    # Migrations run in alphabetical order by filename
    if [ -d "/app/backend/migrations" ]; then
        for migration in /app/backend/migrations/*.py; do
            if [ -f "$migration" ]; then
                migration_name=$(basename "$migration" .py)
                echo ""
                echo "Running migration: $migration_name"
                /app/.venv/bin/python "$migration" || {
                    echo "⚠️  Migration $migration_name failed (may already be applied)"
                }
            fi
        done
        echo ""
        echo "================================"
        echo "Migrations completed!"
        echo "================================"
    else
        echo "No migrations directory found, skipping..."
    fi
else
    echo "Skipping migrations (RUN_MIGRATIONS not set to 'true')"
fi

echo ""
# Start the application
echo "Starting uvicorn server..."
exec /app/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8080}"
