FROM python:3.11-slim

WORKDIR /app

# Install curl for startup.sh
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything (includes startup.sh at root)
COPY . .

# Make startup.sh executable
RUN chmod +x /app/startup.sh

# Run startup script on container start
CMD ["./startup.sh"]
