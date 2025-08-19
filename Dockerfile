FROM python:3.11-slim

# Install system dependencies including git and flyctl
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install flyctl
RUN curl -L https://fly.io/install.sh | sh
ENV PATH="/root/.fly/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs apps/frontend/v4

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the V4 server
CMD ["python", "apps/sophia-api/mcp_server.py"]
