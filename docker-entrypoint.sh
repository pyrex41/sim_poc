#!/bin/bash
set -e

# Ensure DATA directory exists
mkdir -p /data
echo "✓ Data directory ready: /data"

# Run migrations (always on deploy, idempotent operations)
echo ""
echo "================================"
echo "Running database migrations..."
echo "================================"

# Run main migration script (backend/migrate.py)
if [ -f "/app/backend/migrate.py" ]; then
    echo ""
    echo "Running main migration: migrate.py"
    /app/.venv/bin/python /app/backend/migrate.py || {
        echo "⚠️  Main migration failed (may already be applied)"
    }
fi

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
fi

echo ""
echo "================================"
echo "Migrations completed!"
echo "================================"

echo ""
# Start the application
echo "Starting uvicorn server..."
exec /app/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8080}"
