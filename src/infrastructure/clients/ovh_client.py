import requests
from requests.auth import HTTPBasicAuth
from pydantic.networks import IPvAnyAddress


from domain.hostconfig import HostConfig
from infrastructure.config import Config
from infrastructure.logger import Logger

HOST = "https://www.ovh.com"
PATH = "/nic/update"
SYS_PARAM = "dyndns"


class OvhClient:
    """
    Client to update the public IP of a hostname using the OVH API.
    """

    def __init__(self, host: HostConfig):
        """
        Initializes the client with the given host configuration.
        """
        self.logger = Logger().get_logger()
        self.config = Config()
        self.host = host
        self.auth = self._get_auth()

    def _get_auth(self) -> HTTPBasicAuth:
        """
        Creates HTTP basic authentication object from host credentials.
        
        Returns:
            HTTPBasicAuth: Authentication object for OVH API requests.
        """
        self.logger.info(f'{self.host.hostname} | Authenticating as {self.host.username}')
        return HTTPBasicAuth(
            username=self.host.username,
            password=self.host.password.get_secret_value()
        )

    def update_ip(self, new_public_ip: IPvAnyAddress) -> bool:
        """
        Updates the host's public IP address via OVH API.
        
        Args:
            new_public_ip: The new IP address to set for the hostname.
            
        Returns:
            bool: True if the update was successful, False otherwise.
                 Returns None if a request exception occurred.
        """
        url = f'{HOST}{PATH}?system={SYS_PARAM}&hostname={self.host.hostname}&myip={new_public_ip}'

        try:
            self.logger.info(f'{self.host.hostname} | Updating IP')
            response = requests.get(url, auth=self.auth)
            self.logger.info(f'{self.host.hostname} | Update response: {response.status_code} {response.text}')
            
            return response.ok

        except requests.RequestException as e:
            self.logger.error(f'{self.host.hostname} | IP update failed: {e}')
            return None
