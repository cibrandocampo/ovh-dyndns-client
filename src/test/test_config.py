import os
import unittest
from unittest.mock import patch, mock_open

from domain.hostconfig import HostConfig
from infrastructure.config import Config


class TestConfig(unittest.TestCase):
    
    def setUp(self):
        """
        Resets the Config singleton instance before each test to ensure a clean test environment. 
        This ensures that any previous state from other tests does not affect the current test.
        """
        Config._instance = None
    
    @patch.dict(os.environ, {"LOGGER_NAME": "test-logger", "LOGGER_LEVEL": "DEBUG"})
    def test_logger_config(self):
        """
        Tests whether the logger configuration is correctly retrieved from environment variables. 
        The test checks if the values of LOGGER_NAME and LOGGER_LEVEL in the environment are 
        properly assigned to the logger configuration.
        """
        config = Config()
        self.assertEqual(config.logger_config, ("test-logger", "DEBUG"))

    @patch.dict(os.environ, {"UPDATE_INTERVAL": "600"})
    def test_update_ip_interval_valid(self):
        """
        Tests if the update interval is correctly retrieved from the environment variable 
        UPDATE_INTERVAL. The value is expected to be 600 seconds in this case.
        """
        config = Config()
        self.assertEqual(config.update_ip_interval, 600)

    @patch.dict(os.environ, {"UPDATE_INTERVAL": "invalid"})
    def test_update_ip_interval_invalid(self):
        """
        Tests if an invalid UPDATE_INTERVAL (non-numeric value) defaults to the 
        DEFAULT_UPDATE_INTERVAL value. In this case, it should fall back to 300 seconds.
        """
        config = Config()
        self.assertEqual(config.update_ip_interval, 300)  # DEFAULT_UPDATE_INTERVAL
    
    def test_set_and_get_ip(self):
        """
        Tests whether the IP address can be set and retrieved correctly using the set_ip 
        and ip attributes of the Config class.
        """
        config = Config()
        config.set_ip("192.168.1.1")
        self.assertEqual(config.ip, "192.168.1.1")

    @patch("builtins.open", new_callable=mock_open, read_data='[{"hostname": "example.com", "username": "user", "password": "pass"}]')
    @patch("os.path.exists", return_value=True)
    def test_hosts_config_valid(self, mock_exists, mock_file):
        """
        Tests if the hosts configuration is correctly loaded from a JSON file. The test 
        mocks the file reading to simulate valid JSON data, and checks if the configuration 
        is correctly parsed into a list of HostConfig objects with the expected attributes.
        """
        config = Config()
        hosts = config.hosts_config
        self.assertEqual(len(hosts), 1)
        self.assertIsInstance(hosts[0], HostConfig)
        self.assertEqual(hosts[0].hostname, "example.com")
        self.assertEqual(hosts[0].username, "user")
        self.assertEqual(hosts[0].password, "pass")
    
    @patch("builtins.open", new_callable=mock_open, read_data='[{"hostname": "example.com"}]')
    @patch("os.path.exists", return_value=True)
    def test_hosts_config_missing_keys(self, mock_exists, mock_file):
        """
        Tests if invalid host configurations (i.e., missing required keys like username and password) 
        are ignored during the configuration loading process. This test ensures that incomplete entries 
        are not included in the resulting host configurations.
        """
        config = Config()
        hosts = config.hosts_config
        self.assertEqual(len(hosts), 0)  # Should ignore incomplete entries
    
    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_hosts_config_file_not_found(self, mock_file):
        """
        Tests if a FileNotFoundError is raised when the hosts configuration file is missing. 
        The test ensures that the absence of the file is handled correctly by raising the appropriate exception.
        """
        config = Config()
        with self.assertRaises(FileNotFoundError):
            _ = config.hosts_config


if __name__ == "__main__":
    unittest.main()
