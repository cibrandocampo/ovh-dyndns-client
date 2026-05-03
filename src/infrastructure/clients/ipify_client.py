import requests
from pydantic import IPvAnyAddress

from application.ports import IpProvider
from infrastructure.logger import Logger

IPIFY_URL = "https://api.ipify.org"
IPIFY_HTTP_TIMEOUT = (5, 10)  # (connect, read) seconds


class IpifyClient(IpProvider):
    """Client for retrieving the current public IP address using the ipify service.

    Talks to ``https://api.ipify.org`` directly with ``requests`` (the
    ``ipify-py`` package was unmaintained and exposed no timeout). A read
    timeout protects the scheduler thread from hanging on a stuck upstream.
    """

    def __init__(self):
        self.logger = Logger().get_logger()

    def get_public_ip(self) -> IPvAnyAddress:
        """Fetch and validate the current public IP address.

        Raises:
            RuntimeError: If the IP could not be retrieved or is invalid.
        """
        try:
            response = requests.get(IPIFY_URL, timeout=IPIFY_HTTP_TIMEOUT)
            response.raise_for_status()
            ip_str = response.text.strip()
            ip = IPvAnyAddress(ip_str)
            self.logger.info(f"Retrieved public IP: {ip}")
            return ip
        except (requests.RequestException, ValueError) as e:
            self.logger.error(f"Failed to retrieve public IP: {e}")
            raise RuntimeError("Unable to fetch IP from ipify") from e
