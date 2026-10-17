# Dockerfile for Demo Trajectory Generator Service
# Phase 2: Includes web UI for Railway deployment in Phase 3

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY static/ ./static/
COPY vehicle_config.yaml .

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8000

# Run service
# Note: Set APP_PASSWORD environment variable for authentication
# Optional: Set CESIUM_ION_TOKEN for enhanced 3D visualization
CMD ["uvicorn", "trajgen.main:app", "--host", "0.0.0.0", "--port", "8000"]
