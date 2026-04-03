FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set permissions for start.sh
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Start command
# We use start.sh which handles migrations and then starts uvicorn
CMD ["./start.sh"]
