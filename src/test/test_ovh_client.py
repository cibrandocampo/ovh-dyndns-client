import unittest
from unittest.mock import MagicMock, patch

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
    def test_update_ip_success_good(self, mock_get):
        """
        Tests the successful execution of the `update_ip` method with 'good' response.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "good 192.168.1.1"
        mock_response.ok = True
        mock_get.return_value = mock_response

        success, error = self.client.update_ip(self.mock_host, "192.168.1.1")
        self.assertTrue(success)
        self.assertIsNone(error)

        mock_get.assert_called_once()

    @patch("requests.get")
    def test_update_ip_success_nochg(self, mock_get):
        """
        Tests the successful execution of the `update_ip` method with 'nochg' response.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "nochg 192.168.1.1"
        mock_response.ok = True
        mock_get.return_value = mock_response

        success, error = self.client.update_ip(self.mock_host, "192.168.1.1")
        self.assertTrue(success)
        self.assertIsNone(error)

    @patch("requests.get")
    def test_update_ip_failure_badauth(self, mock_get):
        """
        Tests the failure scenario when authentication fails.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "badauth"
        mock_response.ok = True
        mock_get.return_value = mock_response

        success, error = self.client.update_ip(self.mock_host, "192.168.1.1")
        self.assertFalse(success)
        self.assertIn("Authentication failed", error)

    @patch("requests.get")
    def test_update_ip_failure_nohost(self, mock_get):
        """
        Tests the failure scenario when hostname is not found.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "nohost"
        mock_response.ok = True
        mock_get.return_value = mock_response

        success, error = self.client.update_ip(self.mock_host, "192.168.1.1")
        self.assertFalse(success)
        self.assertIn("Hostname not found", error)

    @patch("requests.get")
    def test_update_ip_failure_status_code(self, mock_get):
        """
        Tests the failure scenario when the IP update request returns a non-OK status code.
        """
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.reason = "Bad Request"
        mock_response.text = "bad request"
        mock_response.ok = False
        mock_get.return_value = mock_response

        success, error = self.client.update_ip(self.mock_host, "192.168.1.1")
        self.assertFalse(success)
        self.assertIn("HTTP 400", error)

    @patch("requests.get")
    def test_update_ip_exception(self, mock_get):
        """
        Tests the failure scenario when the request raises an exception.
        """
        mock_get.side_effect = requests.RequestException("Network error")

        success, error = self.client.update_ip(self.mock_host, "192.168.1.1")
        self.assertFalse(success)
        self.assertIn("Connection error", error)

    @patch("requests.get")
    def test_update_ip_handles_timeout(self, mock_get):
        """A `requests.Timeout` must surface as a clean (False, error) tuple, not an unhandled exception."""
        mock_get.side_effect = requests.Timeout("read timed out")

        success, error = self.client.update_ip(self.mock_host, "192.168.1.1")
        self.assertFalse(success)
        self.assertIn("Connection error", error)

    @patch("requests.get")
    def test_update_ip_passes_timeout(self, mock_get):
        """Verifies the OVH HTTP call carries the configured (connect, read) timeout."""
        from infrastructure.clients.ovh_client import OVH_HTTP_TIMEOUT

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "good 192.168.1.1"
        mock_response.ok = True
        mock_get.return_value = mock_response

        self.client.update_ip(self.mock_host, "192.168.1.1")

        # Timeout must be present in kwargs and equal the module constant.
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs.get("timeout"), OVH_HTTP_TIMEOUT)

    @patch("requests.get")
    def test_update_ip_unknown_error(self, mock_get):
        """
        Tests the failure scenario with an unknown error response.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "somethingweird"
        mock_response.ok = True
        mock_get.return_value = mock_response

        success, error = self.client.update_ip(self.mock_host, "192.168.1.1")
        self.assertFalse(success)
        self.assertIn("Unknown error", error)


if __name__ == "__main__":
    unittest.main()
