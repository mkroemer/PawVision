# Dockerfile for PawVision
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    omxplayer \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data persistence
RUN mkdir -p /data/videos /data/youtube_cache /data/youtube_downloads

# Set environment variables
ENV PAWVISION_DEV_MODE=0
ENV PYTHONUNBUFFERED=1

# Expose web interface port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5001/api/status')" || exit 1

# Run the application
CMD ["python", "-m", "pawvision.main"]
