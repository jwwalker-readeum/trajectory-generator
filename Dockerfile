# Dockerfile for Demo Trajectory Generator Service
# Phase 2: Web UI + Phase 3: Railway-ready production deployment

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY static/ ./static/
COPY vehicle_config.yaml .

# Set Python path
ENV PYTHONPATH=/app/src

# Railway provides PORT environment variable
# Default to 8000 for local development
ENV PORT=8000

# Health check for Railway monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/api/health').read()" || exit 1

# Expose port (Railway ignores this but useful for documentation)
EXPOSE $PORT

# Run service with PORT from environment
# Note: Shell form required for environment variable interpolation
# Set APP_PASSWORD environment variable for authentication
# Optional: Set CESIUM_ION_TOKEN for enhanced 3D visualization
CMD uvicorn trajgen.main:app --host 0.0.0.0 --port $PORT
