import os


class Config:
    """
    Handles environment-based configuration for the application.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    @property
    def logger_config(self) -> tuple:
        """
        Retrieves logger configuration from environment variables.

        Returns:
            tuple[str, str]: (logger name, logger level)
        """
        return (
            os.getenv("LOGGER_NAME", "ovh-dyndns"),
            os.getenv("LOGGER_LEVEL", "INFO").upper(),
        )
