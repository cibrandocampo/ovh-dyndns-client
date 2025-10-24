import logging

from infrastructure.config import Config


class Logger:        

    @staticmethod
    def get_logger(name: str = None, level: str = None) -> logging.Logger:
        """
        Retrieves a configured logger instance.

        :param name: Name of the logger. Defaults to the value from the environment variable `LOGGER_NAME`,
                     or 'ovh-dydns' if not set.
        :param level: Logging level as a string (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
                      Defaults to the value from the environment variable `LOGGER_LEVEL`, or 'INFO' if not set.
        :return: A configured logging.Logger instance.
        """

        if not name or not level:
            name, level = Config().logger_config

        logger = logging.getLogger(name)

        if not logger.hasHandlers():
            formatter = logging.Formatter(
                '%(asctime)s (%(name)s) %(levelname)s | %(message)s',
                datefmt='%Y-%m-%dT%H:%M:%S%z'
            )

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            # Set the logging level, ensuring it's valid
            try:
                level_int = getattr(logging, level.upper(), logging.INFO)
            except AttributeError:
                level_int = logging.INFO
            logger.setLevel(level_int)

        return logger
