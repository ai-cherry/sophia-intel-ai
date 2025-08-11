import logging
import json
import os
from datetime import datetime


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger_name": record.name,
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def setup_telemetry():
    """
    Sets up telemetry with JSON logging.
    In a real application, this would also configure metrics and traces
    to be sent to a backend like LGTM/Grafana.
    """
    # Remove any existing handlers
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Add our JSON formatter
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), handlers=[handler])

    print("Telemetry configured with JSON logger.")
    # Placeholder for metrics and tracing initialization
    # from opentelemetry import trace
    # from opentelemetry.sdk.trace import TracerProvider
    # ... etc.
    print("Metrics and tracing providers would be configured here.")


if __name__ == "__main__":
    setup_telemetry()
    logging.info("This is an informational message.")
    logging.warning("This is a warning message.")
    try:
        1 / 0
    except ZeroDivisionError:
        logging.error("Caught an exception.", exc_info=True)
