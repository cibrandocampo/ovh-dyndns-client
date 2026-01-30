import unittest
from unittest.mock import patch, MagicMock
import requests
from requests.auth import HTTPBasicAuth
from domain.hostconfig import HostConfig
from infrastructure.clients.ovh_client import OvhClient
from infrastructure.config import Config


class TestOvhClient(unittest.TestCase):

    def setUp(self):
        """
        Sets up a mock host configuration (`HostConfig`) and an instance of `OvhClient`
        before each test to ensure that the tests have a consistent environment and
        do not rely on external resources or state.
        """
        # Reset Config singleton to ensure clean state
        Config._instance = None

        self.mock_host = HostConfig(hostname="example.com", username="user", password="pass")
        self.client = OvhClient()

    def test_get_auth(self):
        """
        Tests whether the authentication object (`HTTPBasicAuth`) is correctly created
        using the username and password from the mock host configuration.
        The method `_get_auth` should return an `HTTPBasicAuth` instance.
        """
        auth = self.client._get_auth(self.mock_host)

        # Assert that the authentication object is of type `HTTPBasicAuth`
        self.assertIsInstance(auth, HTTPBasicAuth)

        # Assert that the correct username and password are used for authentication
        self.assertEqual(auth.username, "user")
        self.assertEqual(auth.password, "pass")

    @patch("requests.get")
    def test_update_ip_success(self, mock_get):
        """
        Tests the successful execution of the `update_ip` method. The test simulates
        a successful IP update request (status code 200). The method should return True.
        """
        # Mock the response from the requests.get call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "good 192.168.1.1"
        mock_response.ok = True
        mock_get.return_value = mock_response

        # Call the method under test and assert the expected behavior
        result = self.client.update_ip(self.mock_host, "192.168.1.1")
        self.assertTrue(result)

        # Assert that the `requests.get` method was called once
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_update_ip_failure_status_code(self, mock_get):
        """
        Tests the failure scenario when the IP update request returns a non-OK status code.
        The method should return False.
        """
        # Mock the response with a failure status code
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "bad request"
        mock_response.ok = False
        mock_get.return_value = mock_response

        # Call the method and assert it returns False
        result = self.client.update_ip(self.mock_host, "192.168.1.1")
        self.assertFalse(result)

        # Assert that the `requests.get` method was called once
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_update_ip_exception(self, mock_get):
        """
        Tests the failure scenario for the `update_ip` method when the IP update request
        raises a `requests.RequestException`. The method should return False.
        """
        # Simulate a network error (request failure)
        mock_get.side_effect = requests.RequestException("Network error")

        # Call the method and assert it returns False
        result = self.client.update_ip(self.mock_host, "192.168.1.1")
        self.assertFalse(result)

        # Assert that the `requests.get` method was called once
        mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
