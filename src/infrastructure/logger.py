import logging

from infrastructure.config import Config

# Common log format used across all loggers
LOG_FORMAT = '%(asctime)s (%(name)s) %(levelname)s | %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'

# Logger names
BACKEND_LOGGER_NAME = "ovh-dyndns"
API_LOGGER_NAME = "ovh-api"


class ApiLogFormatter(logging.Formatter):
    """Custom formatter that replaces uvicorn logger names with 'ovh-api'."""

    def format(self, record):
        # Replace uvicorn logger names with our API logger name
        original_name = record.name
        if record.name.startswith("uvicorn"):
            record.name = API_LOGGER_NAME
        result = super().format(record)
        record.name = original_name
        return result


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
            formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

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

    @staticmethod
    def get_uvicorn_log_config(level: str = None) -> dict:
        """
        Returns a logging configuration dictionary for uvicorn.

        :param level: Logging level as a string. Defaults to the value from LOGGER_LEVEL env var.
        :return: A logging config dict compatible with uvicorn.
        """
        if not level:
            _, level = Config().logger_config

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "infrastructure.logger.ApiLogFormatter",
                    "format": LOG_FORMAT,
                    "datefmt": LOG_DATE_FORMAT,
                },
                "access": {
                    "()": "infrastructure.logger.ApiLogFormatter",
                    "format": LOG_FORMAT,
                    "datefmt": LOG_DATE_FORMAT,
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["default"],
                    "level": level.upper(),
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": level.upper(),
                    "handlers": ["default"],
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["access"],
                    "level": level.upper(),
                    "propagate": False,
                },
            },
        }
