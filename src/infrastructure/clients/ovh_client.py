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
        Returns an HTTPBasicAuth object using host credentials.
        """
        self.logger.info(f'{self.host.hostname} | Getting basic auth for: {self.host.username}')
        return HTTPBasicAuth(
            username=self.host.username,
            password=self.host.password.get_secret_value()
        )

    def update_ip(self, new_public_ip: IPvAnyAddress) -> str:
        """
        Sends a request to OVH to update the host's public IP address.
        """
        url = f'{HOST}{PATH}?system={SYS_PARAM}&hostname={self.host.hostname}&myip={new_public_ip}'

        try:
            self.logger.info(f'{self.host.hostname} | Updating IP | URL: {url}')
            response = requests.get(url, auth=self.auth)

            if not response.ok:
                response.raise_for_status()

            self.logger.info(f'{self.host.hostname} | IP update successful ({new_public_ip})')
            self.logger.debug(f'{self.host.hostname} | Response: {response.status_code} - {response.text}')
            return response.content.decode('utf-8')

        except requests.RequestException as e:
            self.logger.error(f'{self.host.hostname} | IP update failed: {e}')
            raise RuntimeError("Failed to update IP in OVH")
