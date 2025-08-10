import logging
import json

class JSONLogFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging():
    """
    Sets up JSON logging.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a new handler
    handler = logging.StreamHandler()
    formatter = JSONLogFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# In a real application, you would configure exporters for LGTM (Loki, Grafana, Tempo, Mimir).
# For now, we will just set up the JSON logging.

if __name__ == '__main__':
    setup_logging()
    logging.info("Telemetry service initialized.")
    logging.warning("This is a warning message.")
    try:
        1 / 0
    except ZeroDivisionError:
        logging.exception("A division by zero error occurred.")