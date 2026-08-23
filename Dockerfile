# Dockerfile for PawVision
FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.30 /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    omxplayer \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency metadata first for better caching
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# Copy application code
COPY . .

# Create directories for data persistence
RUN mkdir -p /data/videos /data/youtube_cache /data/youtube_downloads

# Set environment variables
ENV PAWVISION_DEV_MODE=0
ENV PAWVISION_DATA_DIR=/data
ENV PAWVISION_HOST=0.0.0.0
ENV PAWVISION_PORT=5001
ENV PYTHONUNBUFFERED=1

# Expose web interface port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5001/api/status')" || exit 1

# Run the application
CMD ["uv", "run", "--no-sync", "python", "-m", "pawvision.main"]
