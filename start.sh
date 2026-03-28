#!/bin/bash
# Start all MeetStream services in separate Terminal windows (Mac/Linux)

ROOT="$(cd "$(dirname "$0")" && pwd)"

open_window() {
  osascript -e "tell application \"Terminal\"
    do script \"cd '$ROOT' && $1\"
    activate
  end tell"
}

echo "Starting MeetStream services..."

open_window "uv run python server.py"
open_window "uv run uvicorn backend.main:app --port 3000 --reload"
open_window "uv run uvicorn app.server:app --port 8000 --reload"
open_window "cd '$ROOT/dashboard' && npm run dev -- --port 3002"
open_window "ngrok http 3001"

echo "All services launched in separate Terminal windows."
