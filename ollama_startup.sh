#!/bin/sh

# Start the Ollama server in the background
ollama serve &

# Capture the Process ID
PID=$!

# Wait a few seconds for the server to be ready
sleep 5

# Pull the required model
echo "Pulling embedding model: nomic-embed-text"
ollama pull nomic-embed-text

# Wait for the server process to exit
wait $PID