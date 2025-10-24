import unittest
from unittest.mock import patch
from infrastructure.clients.ipify_client import IpifyClient
import ipify


class TestIpifyClient(unittest.TestCase):
    """
    Unit tests for the IpifyClient class, specifically for the get_public_ip method.
    The tests verify the correct behavior of the method when the external ipify service
    returns a valid IP address or throws an exception.
    """
    
    @patch.object(ipify, 'get_ip')
    @patch('infrastructure.logger.Logger.get_logger')
    def test_get_public_ip_success(self, mock_get_logger, mock_get_ip):
        """
        Test the successful retrieval of the public IP.

        This test mocks the ipify.get_ip method to return a predefined IP address
        ('192.168.1.1'). It then checks whether the get_public_ip method returns the
        correct IP and whether the logger's info method was called with the expected message.

        Args:
            mock_get_logger: The mock for the Logger's get_logger method.
            mock_get_ip: The mock for the ipify.get_ip method.
        """
        mock_get_ip.return_value = '192.168.1.1'
        
        client = IpifyClient()
        result = client.get_public_ip()
        self.assertEqual(str(result), '192.168.1.1')
        
        # Assert that the logger's info method was called with the expected log message
        mock_get_logger.return_value.info.assert_called_with("Retrieved public IP: 192.168.1.1")
    
    @patch.object(ipify, 'get_ip')
    @patch('infrastructure.logger.Logger.get_logger')
    def test_get_public_ip_failure(self, mock_get_logger, mock_get_ip):
        """
        Test the failure scenario when ipify.get_ip raises an exception.

        This test mocks the ipify.get_ip method to raise an exception. It then checks
        that the get_public_ip method raises a RuntimeError and verifies that the
        logger's error method is called with the correct error message.

        Args:
            mock_get_logger: The mock for the Logger's get_logger method.
            mock_get_ip: The mock for the ipify.get_ip method.
        """
        mock_get_ip.side_effect = Exception("Network error")
        
        client = IpifyClient()
        
        with self.assertRaises(RuntimeError):
            client.get_public_ip()
        
        # Assert that the logger's error method was called with the expected error message
        mock_get_logger.return_value.error.assert_called_with("Failed to retrieve public IP: Network error")
