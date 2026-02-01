import unittest
from unittest.mock import patch
import logging
from infrastructure.logger import Logger, ApiLogFormatter, LOG_FORMAT, LOG_DATE_FORMAT, API_LOGGER_NAME
from infrastructure.config import Config


class TestLogger(unittest.TestCase):
    
    def setUp(self):
        """
        Reset Config singleton before each test to ensure clean state.
        """
        Config._instance = None
        # Clear any existing loggers to ensure clean state
        import logging
        logging.getLogger().handlers.clear()
        # Remove any existing loggers
        for name in list(logging.Logger.manager.loggerDict.keys()):
            if name.startswith('custom_logger') or name.startswith('test_logger') or name.startswith('invalid_logger'):
                del logging.Logger.manager.loggerDict[name]
    
    def test_get_logger_with_default_values(self):
        """
        Tests that the `get_logger()` method retrieves a logger configured with default values.
        """
        # Remove env vars if they exist to test defaults
        import os
        env_backup = {}
        for key in ["LOGGER_NAME", "LOGGER_LEVEL"]:
            if key in os.environ:
                env_backup[key] = os.environ.pop(key)
        try:
            Config._instance = None  # Reset singleton
            # Get the logger using the method under test
            logger = Logger.get_logger()

            # Assert the logger's name and level are as expected
            self.assertEqual(logger.name, "ovh-dyndns")
            # Default level is INFO when no environment variable is set
            self.assertEqual(logger.level, logging.INFO)

            # Assert the logger has handlers attached
            self.assertTrue(logger.hasHandlers())
        finally:
            # Restore env vars
            os.environ.update(env_backup)
    
    def test_get_logger_with_custom_name_and_level(self):
        """
        Tests that the `get_logger()` method allows setting a custom logger name and logging level. 
        In this case, the logger is expected to be named `"custom_logger"` with a logging level of `"DEBUG"`.
        """
        # Get the logger with custom name and level
        logger = Logger.get_logger(name="custom_logger", level="DEBUG")
        
        # Assert the custom name and level are correctly assigned
        self.assertEqual(logger.name, "custom_logger")
        self.assertEqual(logger.level, logging.DEBUG)
    
    def test_logger_uses_valid_levels(self):
        """
        Tests that the `get_logger()` method correctly assigns valid logging levels. This test iterates over 
        all valid logging levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) and checks if they are 
        correctly mapped to the corresponding logger level constant.
        """
        # Define valid logging levels as a dictionary
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        
        # Test each level with unique names to avoid conflicts
        for i, (level_str, level_const) in enumerate(levels.items()):
            logger = Logger.get_logger(name=f"test_logger_{i}", level=level_str)
            # Assert that the logger's level matches the expected constant
            self.assertEqual(logger.level, level_const)
    
    def test_logger_defaults_to_info_on_invalid_level(self):
        """
        Tests that the `get_logger()` method defaults to the `INFO` level if an invalid logging level 
        (such as `"INVALID"`) is provided.
        """
        # Get the logger with an invalid level
        logger = Logger.get_logger(name="invalid_logger", level="INVALID")
        
        # Assert that the logger defaults to INFO level
        self.assertEqual(logger.level, logging.INFO)
    
    def test_logger_has_formatter(self):
        """
        Tests that the logger created by `get_logger()` method is configured with a formatter.
        The formatter should be set to `'%(asctime)s (%(name)s) %(levelname)s | %(message)s'`.
        """
        # Get the logger
        logger = Logger.get_logger()
        
        # Iterate over all handlers attached to the logger
        for handler in logger.handlers:
            # Assert that the handler has a formatter
            self.assertIsInstance(handler.formatter, logging.Formatter)
            
            # Assert that the formatter's format matches the expected format
            self.assertEqual(handler.formatter._fmt, '%(asctime)s (%(name)s) %(levelname)s | %(message)s')


class TestApiLogFormatter(unittest.TestCase):

    def test_format_replaces_uvicorn_name(self):
        """Tests that uvicorn logger names are replaced with 'ovh-api'."""
        formatter = ApiLogFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        record = logging.LogRecord(
            name="uvicorn.access",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        self.assertIn(f"({API_LOGGER_NAME})", formatted)
        self.assertNotIn("uvicorn", formatted)
        # Verify original name is restored
        self.assertEqual(record.name, "uvicorn.access")

    def test_format_replaces_uvicorn_error_name(self):
        """Tests that uvicorn.error logger name is replaced with 'ovh-api'."""
        formatter = ApiLogFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        record = logging.LogRecord(
            name="uvicorn.error",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Error message",
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        self.assertIn(f"({API_LOGGER_NAME})", formatted)

    def test_format_preserves_non_uvicorn_name(self):
        """Tests that non-uvicorn logger names are preserved."""
        formatter = ApiLogFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        record = logging.LogRecord(
            name="custom-logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        self.assertIn("(custom-logger)", formatted)
        self.assertNotIn(API_LOGGER_NAME, formatted)


class TestUvicornLogConfig(unittest.TestCase):

    def setUp(self):
        Config._instance = None

    def test_get_uvicorn_log_config_returns_dict(self):
        """Tests that get_uvicorn_log_config returns a valid dict."""
        config = Logger.get_uvicorn_log_config()
        self.assertIsInstance(config, dict)
        self.assertEqual(config["version"], 1)
        self.assertIn("formatters", config)
        self.assertIn("handlers", config)
        self.assertIn("loggers", config)

    def test_get_uvicorn_log_config_has_correct_loggers(self):
        """Tests that the config contains uvicorn loggers."""
        config = Logger.get_uvicorn_log_config()
        self.assertIn("uvicorn", config["loggers"])
        self.assertIn("uvicorn.error", config["loggers"])
        self.assertIn("uvicorn.access", config["loggers"])

    def test_get_uvicorn_log_config_uses_custom_formatter(self):
        """Tests that the config uses ApiLogFormatter."""
        config = Logger.get_uvicorn_log_config()
        self.assertEqual(
            config["formatters"]["default"]["()"],
            "infrastructure.logger.ApiLogFormatter"
        )
        self.assertEqual(
            config["formatters"]["access"]["()"],
            "infrastructure.logger.ApiLogFormatter"
        )

    def test_get_uvicorn_log_config_with_custom_level(self):
        """Tests that custom level is applied to uvicorn config."""
        config = Logger.get_uvicorn_log_config(level="DEBUG")
        self.assertEqual(config["loggers"]["uvicorn"]["level"], "DEBUG")
        self.assertEqual(config["loggers"]["uvicorn.error"]["level"], "DEBUG")
        self.assertEqual(config["loggers"]["uvicorn.access"]["level"], "DEBUG")

    @patch.dict('os.environ', {'LOGGER_LEVEL': 'WARNING'})
    def test_get_uvicorn_log_config_uses_env_level(self):
        """Tests that level from environment is used when not specified."""
        Config._instance = None
        config = Logger.get_uvicorn_log_config()
        self.assertEqual(config["loggers"]["uvicorn"]["level"], "WARNING")


if __name__ == "__main__":
    unittest.main()
