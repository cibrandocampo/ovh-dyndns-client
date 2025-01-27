import os
import logging

DEFAUL_LOGGER_NAME = 'ovh-dydns'
DEFAUL_LOGGER_LEVEL = 'INFO'

class Logger:
    """
    Utility class to manage logger instances with consistent configurations.

    This class ensures that all loggers are created with a standardized format and level, avoiding
    duplicate handlers for the same logger. The logging library internally uses a singleton pattern,
    so repeated calls to this method will always return the same logger instance for a given name.

    This design ensures efficient logging and prevents issues like duplicate log entries or
    excessive resource usage.
    """

    @staticmethod
    def get_logger(name: str = None, level: str = None) -> logging.Logger:
        """
        Obtains a logger instance with the given name and configures it if not already configured.

        Args:
            name (str, optional): Name of the logger (defaults to the value of the environment variable
                'DEFAUL_LOGGER_NAME', or 'ovh-dydns' if not set).
            level (str, optional): Logging level as a string (e.g., 'INFO', 'DEBUG'). Defaults to the
                value of the environment variable 'DEFAUL_LOGGER_LEVEL', or 'INFO' if not set.

        Returns:
            logging.Logger: Configured logger instance.

        """
        
        logger = logging.getLogger(name = name or os.environ.get('DEFAUL_LOGGER_NAME', DEFAUL_LOGGER_NAME))
        
        if not logger.hasHandlers():
            formatter = logging.Formatter('%(asctime)s (%(name)s) %(levelname)s | %(message)s',
                                           datefmt='%Y-%m-%dT%H:%M:%S%z')
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            if not level or not level.upper() not in logging._nameToLevel.keys():
                level = os.environ.get('DEFAUL_LOGGER_LEVEL', DEFAUL_LOGGER_LEVEL)

            log_level = getattr(logging, level, logging.INFO)
            logger.setLevel(log_level)

        return logger
