from abc import ABC, abstractmethod

class LoggerService(ABC):
    @abstractmethod
    def info(self, message: str, **kwargs):
        pass

    @abstractmethod
    def error(self, message: str, **kwargs):
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs):
        pass

    @abstractmethod
    def debug(self, message: str, **kwargs):
        pass
