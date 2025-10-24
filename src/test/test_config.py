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
        # Also reset any cached properties
        if hasattr(Config, '_load_hosts_config'):
            Config._load_hosts_config.cache_clear()
    
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
        
        # Test that the singleton maintains state
        config2 = Config()
        self.assertEqual(config2.ip, "192.168.1.1")

    def test_singleton_behavior(self):
        """
        Tests that Config follows singleton pattern - multiple instances should be the same object.
        """
        config1 = Config()
        config2 = Config()
        
        # Should be the same instance
        self.assertIs(config1, config2)
        
        # Changes in one should affect the other
        config1.set_ip("192.168.1.100")
        self.assertEqual(config2.ip, "192.168.1.100")

    def test_singleton_persistence_across_instances(self):
        """
        Tests that the singleton maintains state across different variable references,
        simulating the real-world scenario where UpdateDnsController creates new Config() instances.
        """
        # Simulate first execution
        config1 = Config()
        config1.set_ip("192.168.1.1")
        
        # Simulate second execution (like in UpdateDnsController)
        config2 = Config()
        self.assertEqual(config2.ip, "192.168.1.1")  # Should remember the IP
        
        # Simulate IP change
        config2.set_ip("192.168.1.2")
        
        # Simulate third execution
        config3 = Config()
        self.assertEqual(config3.ip, "192.168.1.2")  # Should remember the new IP

    def test_hosts_config_real_file(self):
        """
        Tests that the hosts configuration loads the real file correctly.
        This test verifies that the configuration system works with the actual hosts.json file.
        """
        config = Config()
        hosts = config.hosts_config
        self.assertGreater(len(hosts), 0)  # Should have at least one host
        self.assertIsInstance(hosts[0], HostConfig)
        # Verify that all hosts have required fields
        for host in hosts:
            self.assertIsNotNone(host.hostname)
            self.assertIsNotNone(host.username)
            self.assertIsNotNone(host.password)
    
    def test_hosts_config_validation(self):
        """
        Tests that the hosts configuration validates required fields.
        This test verifies that the configuration system properly validates host entries.
        """
        config = Config()
        hosts = config.hosts_config
        # All hosts should be valid HostConfig objects
        for host in hosts:
            self.assertIsInstance(host, HostConfig)
            self.assertIsNotNone(host.hostname)
            self.assertIsNotNone(host.username)
            self.assertIsNotNone(host.password)
    
    def test_hosts_config_file_exists(self):
        """
        Tests that the hosts configuration file exists and is accessible.
        This test verifies that the configuration system can access the hosts file.
        """
        config = Config()
        # This should not raise an exception if the file exists
        hosts = config.hosts_config
        self.assertIsInstance(hosts, list)


if __name__ == "__main__":
    unittest.main()
