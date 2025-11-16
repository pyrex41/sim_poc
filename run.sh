#!/bin/bash
# Run the backend server using uvicorn with proper module path

echo "Starting Physics Simulator API server..."
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
