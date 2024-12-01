import abc

from loguru import logger


class Notifier:
    @staticmethod
    @abc.abstractmethod
    def notify(message: str) -> None:
        raise NotImplementedError


class ConsoleNotifier(Notifier):
    @staticmethod
    def notify(message: str) -> None:
        logger.info(message)
