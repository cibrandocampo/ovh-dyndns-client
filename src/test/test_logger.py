import unittest
from unittest.mock import patch
import logging
from infrastructure.logger import Logger


class TestLogger(unittest.TestCase):
    
    @patch("infrastructure.config.Config")
    def test_get_logger_with_default_values(self, mock_config):
        """
        Tests that the `get_logger()` method retrieves a logger configured with default values 
        from the `Config` class. The mock simulates the default logger configuration values 
        (`"ovh-dydns"` for logger name and `"INFO"` for logging level).

        The test checks that the logger has the correct name, logging level, and handlers.
        """
        # Mock the Config class and set the logger config
        mock_config_instance = mock_config.return_value
        mock_config_instance.logger_config = ("ovh-dydns", "INFO")
        
        # Get the logger using the method under test
        logger = Logger.get_logger()
        
        # Assert the logger's name and level are as expected
        self.assertEqual(logger.name, "ovh-dydns")
        self.assertEqual(logger.level, logging.INFO)
        
        # Assert the logger has handlers attached
        self.assertTrue(logger.hasHandlers())
    
    @patch("infrastructure.config.Config")
    def test_get_logger_with_custom_name_and_level(self, mock_config):
        """
        Tests that the `get_logger()` method allows setting a custom logger name and logging level. 
        In this case, the logger is expected to be named `"custom_logger"` with a logging level of `"DEBUG"`.
        """
        # Get the logger with custom name and level
        logger = Logger.get_logger(name="custom_logger", level="DEBUG")
        
        # Assert the custom name and level are correctly assigned
        self.assertEqual(logger.name, "custom_logger")
        self.assertEqual(logger.level, logging.DEBUG)
    
    @patch("infrastructure.config.Config")
    def test_logger_uses_valid_levels(self, mock_config):
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
        
        # Test each level
        for level_str, level_const in levels.items():
            logger = Logger.get_logger(name="test_logger", level=level_str)
            # Assert that the logger's level matches the expected constant
            self.assertEqual(logger.level, level_const)
    
    @patch("infrastructure.config.Config")
    def test_logger_defaults_to_info_on_invalid_level(self, mock_config):
        """
        Tests that the `get_logger()` method defaults to the `INFO` level if an invalid logging level 
        (such as `"INVALID"`) is provided.
        """
        # Get the logger with an invalid level
        logger = Logger.get_logger(name="invalid_logger", level="INVALID")
        
        # Assert that the logger defaults to INFO level
        self.assertEqual(logger.level, logging.INFO)
    
    @patch("infrastructure.config.Config")
    def test_logger_has_formatter(self, mock_config):
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


if __name__ == "__main__":
    unittest.main()
