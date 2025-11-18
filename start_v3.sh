#!/bin/bash
# Startup script for Generation Platform v3

set -e

echo "===================================================================="
echo "Generation Platform v3 - Startup"
echo "===================================================================="

# Check if v3 database exists
if [ ! -f "backend/simulator_v3.db" ]; then
    echo "✗ v3 database not found"
    echo ""
    echo "Running migration to create v3 database..."
    python3 backend/migrate_to_v3.py
    echo ""
fi

echo "✓ v3 database ready"
echo ""

# Check for required environment variables
if [ -z "$REPLICATE_API_KEY" ]; then
    echo "⚠ WARNING: REPLICATE_API_KEY not set"
    echo "  Image generation will fail without a valid API key"
    echo "  Set it with: export REPLICATE_API_KEY='your-key-here'"
    echo ""
fi

echo "Starting Generation Platform v3..."
echo ""
echo "API will be available at:"
echo "  - http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo ""
echo "===================================================================="
echo ""

# Start the server
python3 -m uvicorn backend.main_v3:app --host 0.0.0.0 --port 8000 --reload
