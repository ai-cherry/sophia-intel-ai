# MCP Server - Memory and Tool Management Service
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements from mcp-server directory
COPY pulumi/mcp-server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install additional MCP dependencies
RUN pip install --no-cache-dir \
    fastapi[all] \
    uvicorn[standard] \
    redis \
    psycopg2-binary \
    weaviate-client \
    python-dotenv \
    sqlalchemy \
    sqlite-fts4

# Copy application code from correct paths
COPY pulumi/mcp-server/src/ ./src/
COPY pulumi/mcp-server/ ./

# Create non-root user
RUN useradd -m -u 1000 sophia && \
    mkdir -p /data && \
    chown -R sophia:sophia /app /data
USER sophia

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# Expose port
EXPOSE 8004

# Start the MCP server
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004", "--reload"]