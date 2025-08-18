FROM python:3.12-slim

WORKDIR /app

# Copy production requirements
COPY requirements-production-clean.txt requirements.txt

# Install dependencies with no cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy production backend
COPY sophia_production_clean.py main.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Use uvicorn with production backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

