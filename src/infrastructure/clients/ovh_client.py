import requests
from requests.auth import HTTPBasicAuth

from domain.hostconfig import HostConfig
from infrastructure.config import Config
from infrastructure.logger import Logger


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
        self.logger.debug(f'Updating IP for hostname: {self.host.hostname}')

        host = self.config.get('ovh_config', 'HOST')
        path = self.config.get('ovh_config', 'PATH')
        sys_param = self.config.get('ovh_config', 'SYS_PARAM')

        url = f'{host}{path}?system={sys_param}&hostname={self.host.hostname}&myip={new_public_ip}'

        try:
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
            
            self.logger.info(f'Successfully updated IP for hostname: {self.host.hostname} with response: {response.text}')
            return response.content.decode('utf8')
        
        except requests.RequestException as e:
            self.logger.error(f'Failed to update IP for hostname: {self.host.hostname}: {e}')
            raise RuntimeError("Failed to update IP in OVH")
