import unittest
from unittest.mock import patch, MagicMock
import requests
from requests.auth import HTTPBasicAuth
from domain.hostconfig import HostConfig
from infrastructure.clients.ovh_client import OvhClient


class TestOvhClient(unittest.TestCase):
    
    def setUp(self):
        """
        Sets up a mock host configuration (`HostConfig`) and an instance of `OvhClient` 
        before each test to ensure that the tests have a consistent environment and 
        do not rely on external resources or state.
        """
        self.mock_host = HostConfig(hostname="example.com", username="user", password="pass")
        self.client = OvhClient(self.mock_host)
    
    def test_get_auth(self):
        """
        Tests whether the authentication object (`HTTPBasicAuth`) is correctly created 
        using the username and password from the mock host configuration.
        The method `_get_auth` should return an `HTTPBasicAuth` instance.
        """
        auth = self.client._get_auth()
        
        # Assert that the authentication object is of type `HTTPBasicAuth`
        self.assertIsInstance(auth, HTTPBasicAuth)
        
        # Assert that the correct username and password are used for authentication
        self.assertEqual(auth.username, "user")
        self.assertEqual(auth.password, "pass")
    
    @patch("requests.get")
    def test_update_ip_success(self, mock_get):
        """
        Tests the successful execution of the `update_ip` method. The test simulates 
        a successful IP update request (status code 200 and correct response text).
        The method should return the correct IP address response.
        """
        # Mock the response from the requests.get call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "good 192.168.1.1"
        mock_response.content.decode.return_value = "good 192.168.1.1"
        mock_get.return_value = mock_response
        
        # Call the method under test and assert the expected behavior
        response = self.client.update_ip("192.168.1.1")
        self.assertEqual(response, "good 192.168.1.1")
        
        # Assert that the `requests.get` method was called once
        mock_get.assert_called_once()
    
    @patch("requests.get")
    def test_update_ip_failure(self, mock_get):
        """
        Tests the failure scenario for the `update_ip` method when the IP update request 
        fails (i.e., raises a `requests.RequestException`). The method should raise 
        a `RuntimeError` with the appropriate error message.
        """
        # Simulate a network error (request failure)
        mock_get.side_effect = requests.RequestException("Network error")
        
        # Assert that a `RuntimeError` is raised with the correct error message
        with self.assertRaises(RuntimeError) as context:
            self.client.update_ip("192.168.1.1")
        
        self.assertEqual(str(context.exception), "Failed to update IP in OVH")
        
        # Assert that the `requests.get` method was called once
        mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
