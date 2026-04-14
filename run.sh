#!/bin/bash

# Run the Ultimate Advisor API with uvicorn
# Default host: 0.0.0.0, port: 8000

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8825}"
RELOAD="${RELOAD:---reload}"

echo "🚀 Starting Ultimate Advisor API..."
echo "📍 Host: $HOST"
echo "📍 Port: $PORT"
echo ""

uvicorn src.main:app --host "$HOST" --port "$PORT" $RELOAD
