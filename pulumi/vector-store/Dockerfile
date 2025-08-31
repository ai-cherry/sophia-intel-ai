# Vector Store Service - Modern Embeddings & Search
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

# Copy requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install vector store dependencies
RUN pip install --no-cache-dir \
    fastapi[all] \
    uvicorn[standard] \
    weaviate-client \
    qdrant-client \
    sentence-transformers \
    transformers \
    torch \
    numpy \
    python-dotenv

# Copy application code
COPY src/ ./src/
COPY . ./

# Create non-root user
RUN useradd -m -u 1000 sophia && chown -R sophia:sophia /app
USER sophia

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

# Expose port
EXPOSE 8005

# Start the vector store service
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005", "--reload"]