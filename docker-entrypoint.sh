#!/bin/bash
set -e

echo "==================================="
echo "Atelier - Starting"
echo "==================================="

# Initialize database (creates tables if not exist)
echo "Initializing database..."
python -m src.cli init

# Migrate image paths to portable relative format (one-time operation)
# Converts any absolute paths (Windows or Linux) to relative paths
# that work across all environments (Windows dev, Docker, etc.)
echo "Ensuring image paths are in portable format..."
python scripts/fix_paths.py /app/data/artworks.db

# Check if scheduler should be enabled
if [ "$ENABLE_SCHEDULER" = "true" ]; then
    echo "Starting scheduler in background (interval: ${SCRAPE_INTERVAL_MINUTES:-60} minutes)..."
    python -m src.cli scheduler &
    SCHEDULER_PID=$!
    echo "Scheduler started with PID: $SCHEDULER_PID"
fi

# Start the web server
echo "Starting web server on ${API_HOST:-0.0.0.0}:${API_PORT:-8000}..."
exec python -m src.cli server
