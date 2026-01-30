import requests
from requests.auth import HTTPBasicAuth
from pydantic.networks import IPvAnyAddress

from domain.hostconfig import HostConfig
from infrastructure.logger import Logger
from application.ports import DnsUpdater

HOST = "https://www.ovh.com"
PATH = "/nic/update"
SYS_PARAM = "dyndns"


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

    def update_ip(self, host: HostConfig, ip: IPvAnyAddress) -> bool:
        """
        Updates the host's public IP address via OVH API.

        Args:
            host: Host configuration to update.
            ip: The new IP address to set for the hostname.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        url = f'{HOST}{PATH}?system={SYS_PARAM}&hostname={host.hostname}&myip={ip}'
        auth = self._get_auth(host)

        try:
            self.logger.info(f'{host.hostname} | Updating IP')
            response = requests.get(url, auth=auth)
            self.logger.info(f'{host.hostname} | Update response: {response.status_code} {response.text}')

            return response.ok

        except requests.RequestException as e:
            self.logger.error(f'{host.hostname} | IP update failed: {e}')
            return False
