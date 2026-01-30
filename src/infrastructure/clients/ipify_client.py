import ipify
from pydantic import IPvAnyAddress
from infrastructure.logger import Logger
from application.ports import IpProvider


class IpifyClient(IpProvider):
    """
    Client for retrieving the current public IP address using the ipify service.
    """

    def __init__(self):
        """
        Initializes the IpifyClient with a logger instance.
        """
        self.logger = Logger().get_logger()

    def get_public_ip(self) -> IPvAnyAddress:
        """
        Fetches and validates the current public IP address.

        Returns:
            IPvAnyAddress: A validated IP address (IPv4 or IPv6).

        Raises:
            RuntimeError: If the IP could not be retrieved or is invalid.
        """
        try:
            ip_str = ipify.get_ip()
            ip = IPvAnyAddress(ip_str)
            self.logger.info(f"Retrieved public IP: {ip}")
            return ip
        except Exception as e:
            self.logger.error(f"Failed to retrieve public IP: {e}")
            raise RuntimeError("Unable to fetch IP from ipify")
