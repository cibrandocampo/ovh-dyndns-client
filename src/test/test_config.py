import os
import unittest
from unittest.mock import patch

from infrastructure.config import Config


class TestConfig(unittest.TestCase):

    def setUp(self):
        """Reset the Config singleton instance before each test."""
        Config._instance = None

    @patch.dict(os.environ, {"LOGGER_NAME": "test-logger", "LOGGER_LEVEL": "DEBUG"})
    def test_logger_config(self):
        """Test that logger configuration is correctly retrieved from environment variables."""
        config = Config()
        self.assertEqual(config.logger_config, ("test-logger", "DEBUG"))

    @patch.dict(os.environ, {"LOGGER_NAME": "custom", "LOGGER_LEVEL": "warning"})
    def test_logger_config_case_insensitive(self):
        """Test that logger level is converted to uppercase."""
        config = Config()
        self.assertEqual(config.logger_config, ("custom", "WARNING"))

    def test_logger_config_defaults(self):
        """Test that logger configuration uses defaults when env vars are not set."""
        config = Config()
        name, level = config.logger_config
        self.assertEqual(name, "ovh-dydns")
        self.assertEqual(level, "INFO")

    def test_singleton_behavior(self):
        """Test that Config follows singleton pattern."""
        config1 = Config()
        config2 = Config()
        self.assertIs(config1, config2)


if __name__ == "__main__":
    unittest.main()
