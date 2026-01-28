import logging
import os
import sys
from typing import Any, Dict

def setup_logging():
    """
    Configures the Global Logging State.
    Ensures that distinct loggers (uvicorn, uvicorn.access, app) use the same handler and formatter.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Standard format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)

    # Handler that writes to stderr (standard for containerized apps)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    # List of loggers to configure
    loggers = [
        logging.getLogger("uvicorn"),
        logging.getLogger("uvicorn.access"),
        logging.getLogger("uvicorn.error"),
        logging.getLogger("fastapi"),
        logging.getLogger("advisor") # Our app logger
    ]

    # Configure root logger
    logging.getLogger().handlers = [handler]
    logging.getLogger().setLevel(numeric_level)
    
    for logger in loggers:
        # Clear existing handlers to avoid duplicates
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(numeric_level)
        # Prevent propagation to avoid double logging if root captures it
        logger.propagate = False 

    # Uvicorn access log is special, let's make sure it's consistent
    logging.getLogger("uvicorn.access").setLevel(numeric_level)

