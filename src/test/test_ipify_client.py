import unittest
from unittest.mock import MagicMock, patch

import requests

from infrastructure.clients.ipify_client import IPIFY_HTTP_TIMEOUT, IPIFY_URL, IpifyClient


class TestIpifyClient(unittest.TestCase):
    """Unit tests for ``IpifyClient.get_public_ip``.

    The client now talks to ``https://api.ipify.org`` directly via
    ``requests``; tests mock the underlying HTTP call.
    """

    @patch("infrastructure.clients.ipify_client.requests.get")
    @patch("infrastructure.logger.Logger.get_logger")
    def test_get_public_ip_success(self, mock_get_logger, mock_get):
        """Successful retrieval returns the parsed IP and is logged."""
        mock_response = MagicMock(text="192.168.1.1")
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = IpifyClient()
        result = client.get_public_ip()

        self.assertEqual(str(result), "192.168.1.1")
        mock_get.assert_called_once_with(IPIFY_URL, timeout=IPIFY_HTTP_TIMEOUT)
        mock_get_logger.return_value.info.assert_called_with("Retrieved public IP: 192.168.1.1")

    @patch("infrastructure.clients.ipify_client.requests.get")
    @patch("infrastructure.logger.Logger.get_logger")
    def test_get_public_ip_strips_whitespace(self, mock_get_logger, mock_get):
        """Trailing whitespace from the upstream response must not break IP parsing."""
        mock_response = MagicMock(text="10.0.0.1\n")
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = IpifyClient()
        result = client.get_public_ip()
        self.assertEqual(str(result), "10.0.0.1")

    @patch("infrastructure.clients.ipify_client.requests.get")
    @patch("infrastructure.logger.Logger.get_logger")
    def test_get_public_ip_raises_on_request_exception(self, mock_get_logger, mock_get):
        """Network errors from ``requests`` are wrapped in ``RuntimeError``."""
        mock_get.side_effect = requests.RequestException("Network error")

        client = IpifyClient()
        with self.assertRaises(RuntimeError):
            client.get_public_ip()
        mock_get_logger.return_value.error.assert_called_with("Failed to retrieve public IP: Network error")

    @patch("infrastructure.clients.ipify_client.requests.get")
    @patch("infrastructure.logger.Logger.get_logger")
    def test_get_public_ip_raises_on_timeout(self, mock_get_logger, mock_get):
        """A read timeout must bubble up as a RuntimeError, not freeze the scheduler."""
        mock_get.side_effect = requests.Timeout("read timed out")

        client = IpifyClient()
        with self.assertRaises(RuntimeError):
            client.get_public_ip()

    @patch("infrastructure.clients.ipify_client.requests.get")
    @patch("infrastructure.logger.Logger.get_logger")
    def test_get_public_ip_raises_on_invalid_ip(self, mock_get_logger, mock_get):
        """Non-IP responses (HTML error page, garbage) are also handled cleanly."""
        mock_response = MagicMock(text="not-an-ip")
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = IpifyClient()
        with self.assertRaises(RuntimeError):
            client.get_public_ip()


if __name__ == "__main__":
    unittest.main()
