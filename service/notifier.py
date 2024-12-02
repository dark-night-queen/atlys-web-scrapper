import abc

from loguru import logger


class Notifier:
    @staticmethod
    @abc.abstractmethod
    def notify(message: str) -> None:
        """
        Notify the user about the message
        :param message:
        """
        raise NotImplementedError


class ConsoleNotifier(Notifier):
    @staticmethod
    def notify(message: str) -> None:
        """
        Notify the user about the message using console
        :param message:
        """
        logger.info(message)
