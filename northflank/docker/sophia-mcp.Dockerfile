# SOPHIA MCP Services Dockerfile for Northflank
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash sophia
RUN chown -R sophia:sophia /app
USER sophia

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8001}/health || exit 1

# Expose port (will be overridden by environment)
EXPOSE 8001

# Start command - will be determined by MCP_SERVICE_TYPE environment variable
CMD ["python", "-c", "import os; exec(open(f'mcp_servers/{os.environ.get(\"MCP_SERVICE_TYPE\", \"memory\")}_service.py').read())"]

