import datetime
import logging
import logging.handlers
import os

from settings import logs_path


class LoggerMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Logger(metaclass=LoggerMeta):

    def __calculateExecutionNumber(self):
        return len(os.listdir(logs_path))

    def __init__(self):
        self.__filename = os.path.join(
            logs_path,
            f"{datetime.date.today().isoformat()}_campos_tmc_{self.__calculateExecutionNumber()}.log",
        )

    def getLogger(self, log_name: str = "LoggerId"):
        # Gets the log with the LoggerId
        logger = logging.getLogger(log_name)

        # Create a new logger handler if one is not already created
        if len(logger.handlers) == 0:
            # Prepare the file name based on the date
            fh = logging.handlers.RotatingFileHandler(self.__filename, encoding="utf-8")
            console_handler = logging.StreamHandler()

            # Set the logger level to DEBUG
            logger.setLevel(logging.DEBUG)

            # Prepares the format of the message
            formatter = logging.Formatter(
                "%(asctime)s  [%(funcName)s] %(levelname)s: %(message)s"
            )
            fh.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add the handler to the logger
            logger.addHandler(fh)
            logger.addHandler(console_handler)
        return logger
