import requests
from requests.auth import HTTPBasicAuth

from domain.hostconfig import HostConfig
from infrastructure.config import Config
from infrastructure.logger import Logger

HOST = "https://www.ovh.com"
PATH = "/nic/update"
SYS_PARAM = "dyndns"


class OvhClient:
    """
    Client for interacting with OVH API to update the IP address of a specified host.

    Attributes:
        host (HostConfig): The host configuration containing details like hostname and credentials.
        auth (HTTPBasicAuth): The authentication object for the OVH API.
    """

    def __init__(self, host: HostConfig):
        """
        Initializes the OvhClient with the given host configuration.

        Args:
            host (HostConfig): An instance of HostConfig containing the host details.
        """
        self.logger = Logger().get_logger()
        self.config = Config()
        self.host = host
        self.auth = self._get_auth()

    def _get_auth(self) -> HTTPBasicAuth:
        """
        Generates the HTTPBasicAuth object using the provided username and password.

        Returns:
            HTTPBasicAuth: An authentication object for making API requests.
        """
        self.logger.info(f'{self.host.hostname} | Getting basic auth for: {self.host.username}')
        return HTTPBasicAuth(username=self.host.username, password=self.host.password)

    def update_ip(self, new_public_ip: str) -> str:
        """
        Updates the public IP address of the host on OVH by making a GET request to their API.

        Args:
            new_public_ip (str): The new public IP address to be updated on OVH.

        Returns:
            str: The response content from the OVH API after attempting to update the IP.

        Raises:
            RuntimeError: If the IP update request fails.
        """
        url = f'{HOST}{PATH}?system={SYS_PARAM}&hostname={self.host.hostname}&myip={new_public_ip}'

        try:
            self.logger.info(f'{self.host.hostname} | Requesting update ip | URL: {url}')

            response = requests.get(url, auth=self.auth)
            if not response.ok:
                response.raise_for_status()
            
            self.logger.info(f'{self.host.hostname} | Successfully updated IP ({new_public_ip})')
            self.logger.debug(f'{self.host.hostname} | Response: {response.status_code} - {response.text}')
            return response.content.decode('utf8')
        
        except requests.RequestException as e:
            self.logger.error(f'Failed to update IP for hostname: {self.host.hostname}: {e}')
            raise RuntimeError("Failed to update IP in OVH")
