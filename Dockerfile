# Multi-stage build for optimal size and security
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 agno && \
    mkdir -p /app/tmp && \
    chown -R agno:agno /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/agno/.local

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=agno:agno app/ ./app/
COPY --chown=agno:agno agent-ui/ ./agent-ui/

# Switch to non-root user
USER agno

# Update PATH
ENV PATH=/home/agno/.local/bin:$PATH

# Environment variables (defaults)
ENV AGENT_API_PORT=8003 \
    PLAYGROUND_URL=http://localhost:7777 \
    MCP_FILESYSTEM=true \
    MCP_GIT=true \
    MCP_SUPERMEMORY=true \
    GRAPHRAG_ENABLED=true \
    HYBRID_SEARCH=true \
    EVALUATION_GATES=true \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${AGENT_API_PORT}/healthz || exit 1

# Expose port
EXPOSE 8003

# Labels
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.source="https://github.com/ai-cherry/sophia-intel-ai" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="AI Cherry" \
      org.opencontainers.image.title="Sophia Intel AI" \
      org.opencontainers.image.description="Unified Agent API with MCP, embeddings, and evaluation gates"

# Run the SuperOrchestrator or unified server based on environment
CMD ["sh", "-c", "if [ \"$RUN_MODE\" = \"orchestrator\" ]; then python -m app.core.super_orchestrator; else python -m app.api.unified_server; fi"]
