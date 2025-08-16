FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn pydantic

COPY working_api.py .

EXPOSE 5000

CMD ["python", "working_api.py"]
