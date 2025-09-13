# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install curl and other necessary packages
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --timeout=600 --index-url https://pypi.org/simple -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Copy the startup script and make it executable
COPY startup.sh .
RUN chmod +x startup.sh

# Command to run the startup script
CMD ["./startup.sh"]
