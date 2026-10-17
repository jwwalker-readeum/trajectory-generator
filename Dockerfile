# Dockerfile for Demo Trajectory Generator Service
# Structured for easy Railway deployment in Phase 3

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY vehicle_config.yaml .

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8000

# Run service
CMD ["uvicorn", "trajgen.main:app", "--host", "0.0.0.0", "--port", "8000"]
