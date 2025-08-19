FROM python:3.12-slim

# Expose port
EXPOSE 8080

# Environment variables for optimization
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install flyctl for autonomous deployment
RUN curl -L https://fly.io/install.sh | sh
ENV PATH="/root/.fly/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set working directory
WORKDIR /app

# Copy application code
COPY . /app

# Create non-root user for security and copy flyctl
RUN adduser -u 5678 --disabled-password --gecos "" appuser && \
    mkdir -p /home/appuser/.fly/bin && \
    cp /root/.fly/bin/flyctl /home/appuser/.fly/bin/ && \
    chown -R appuser:appuser /home/appuser/.fly && \
    chown -R appuser /app

USER appuser
ENV PATH="/home/appuser/.fly/bin:$PATH"

# Run the application
CMD ["python", "apps/sophia-api/mcp_server.py"]

