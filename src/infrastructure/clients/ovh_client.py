import requests
from requests.auth import HTTPBasicAuth
from typing import Tuple, Optional
from pydantic.networks import IPvAnyAddress

from domain.hostconfig import HostConfig
from infrastructure.logger import Logger
from application.ports import DnsUpdater

HOST = "https://www.ovh.com"
PATH = "/nic/update"
SYS_PARAM = "dyndns"

# OVH DynHost response codes
RESPONSE_MESSAGES = {
    "good": "IP updated successfully",
    "nochg": "IP unchanged (already set)",
    "nohost": "Hostname not found - check DynHost configuration in OVH",
    "badauth": "Authentication failed - check username/password",
    "notfqdn": "Invalid hostname format",
    "abuse": "Too many requests - try again later",
    "911": "OVH service error - try again later",
    "badagent": "Invalid request",
}


class OvhClient(DnsUpdater):
    """
    Client to update the public IP of a hostname using the OVH API.
    """

    def __init__(self):
        """
        Initializes the client with a logger instance.
        """
        self.logger = Logger().get_logger()

    def _get_auth(self, host: HostConfig) -> HTTPBasicAuth:
        """
        Creates HTTP basic authentication object from host credentials.

        Args:
            host: Host configuration with credentials.

        Returns:
            HTTPBasicAuth: Authentication object for OVH API requests.
        """
        self.logger.info(f'{host.hostname} | Authenticating as {host.username}')
        return HTTPBasicAuth(
            username=host.username,
            password=host.password.get_secret_value()
        )

    def _parse_response(self, response_text: str) -> Tuple[bool, Optional[str]]:
        """
        Parse the OVH DynHost API response.

        Args:
            response_text: Raw response text from OVH API.

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        response_text = response_text.strip().lower()

        # Success cases
        if response_text.startswith("good") or response_text.startswith("nochg"):
            return True, None

        # Error cases - extract the error code
        error_code = response_text.split()[0] if response_text else "unknown"
        error_message = RESPONSE_MESSAGES.get(error_code, f"Unknown error: {response_text}")

        return False, error_message

    def update_ip(self, host: HostConfig, ip: IPvAnyAddress) -> Tuple[bool, Optional[str]]:
        """
        Updates the host's public IP address via OVH API.

        Args:
            host: Host configuration to update.
            ip: The new IP address to set for the hostname.

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        url = f'{HOST}{PATH}?system={SYS_PARAM}&hostname={host.hostname}&myip={ip}'
        auth = self._get_auth(host)

        try:
            self.logger.info(f'{host.hostname} | Updating IP to {ip}')
            response = requests.get(url, auth=auth)
            self.logger.info(f'{host.hostname} | Response: {response.status_code} {response.text}')

            if not response.ok:
                return False, f"HTTP {response.status_code}: {response.reason}"

            return self._parse_response(response.text)

        except requests.RequestException as e:
            self.logger.error(f'{host.hostname} | Request failed: {e}')
            return False, f"Connection error: {str(e)}"
