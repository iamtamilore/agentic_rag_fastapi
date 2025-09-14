#!/bin/sh
set -e

# Wait for Ollama service to be fully up and running
echo "--- Waiting for Ollama service to be ready ---"
until curl -s "http://ollama:11434" > /dev/null; do
  echo "Ollama is unavailable - sleeping"
  sleep 5
done
echo "Ollama service is ready!"

# Pull the required models using Ollama API
echo "--- Pulling LLM models ---"
curl -s -X POST http://ollama:11434/api/pull -d '{"name":"nomic-embed-text"}'
curl -s -X POST http://ollama:11434/api/pull -d '{"name":"llama3.1"}'

# Run the data ingestion script
echo "--- Running data ingestion ---"
python3 src/ingestion.py
echo "--- Ingestion complete ---"