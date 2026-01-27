import logging
from app.services.logger_service import LoggerService

class StdLogger(LoggerService):
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("advisor")

    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=kwargs)
