FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data data/logs data/cache

# Run startup validation
RUN python startup_check.py || true

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health/live').raise_for_status()" || exit 1

# Set environment variables
ENV TBCV_SYSTEM_ENVIRONMENT=production \
    TBCV_SYSTEM_DEBUG=false \
    TBCV_SYSTEM_LOG_LEVEL=info \
    TBCV_SERVER_HOST=0.0.0.0 \
    TBCV_SERVER_PORT=8080

# Run the application
CMD ["python", "main.py", "--mode", "api", "--host", "0.0.0.0", "--port", "8080"]
