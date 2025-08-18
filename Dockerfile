FROM python:3.12-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt requirements.txt

# Install dependencies with no cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy enhanced backend with OpenRouter LLM integration
COPY minimal_main.py main.py

# Copy dashboard static files
COPY apps/dashboard/dist apps/dashboard/dist

EXPOSE 8000

# Use uvicorn with enhanced backend
CMD ["python", "main.py"]

