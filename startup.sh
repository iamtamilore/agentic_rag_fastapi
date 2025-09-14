#!/bin/sh
set -e

# Wait for Ollama service to be fully up and running
echo "--- Waiting for Ollama service to be ready ---"
until curl -s "http://ollama:11434" > /dev/null; do
  echo "Ollama is unavailable - sleeping"
  sleep 5
done
echo "Ollama service is ready!"

# Start the FastAPI server
echo "--- Starting FastAPI server ---"
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
