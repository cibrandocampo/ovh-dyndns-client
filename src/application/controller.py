from typing import List
from domain.hostconfig import HostConfig
from infrastructure.config import Config
from infrastructure.logger import Logger
from infrastructure.clients.ipify_client import IpifyClient
from infrastructure.clients.ovh_client import OvhClient

class UpdateDnsController:
    def __init__(self):
        self.ipify_client = IpifyClient()
        self.logger = Logger().get_logger()
        self.config = Config()
        self.failed_hosts: List[HostConfig] = []

    def handler(self):
        """
        Main handler that orchestrates the DNS update process.
        
        Retrieves the current public IP, compares it with the stored IP,
        and updates DNS records if the IP has changed or retries failed hosts.
        
        Raises:
            RuntimeError: If the DNS update process fails.
        """
        self.logger.info("Starting DNS update process")
        
        try:
            ip = self.ipify_client.get_public_ip()
            if ip == self.config.ip:
                self.logger.info("IP unchanged, skipping update")
                if self.failed_hosts:
                    self.logger.info("Retrying failed hosts")
                    self.update_hosts_ip(self.failed_hosts)
            else:
                self.logger.info("IP changed, updating hosts")
                self.config.set_ip(new_ip=ip)
                self.update_hosts_ip(self.config.hosts_config)

        except Exception as e:
            self.logger.error(f"DNS update error: {e}")
            raise RuntimeError("DynDNS update failed")

    def update_hosts_ip(self, hosts: List[HostConfig]) -> None:
        """
        Updates the IP address for a list of hosts.
        
        Attempts to update each host's DNS record with the current IP.
        Failed updates are tracked in self.failed_hosts for retry.
        
        Args:
            hosts: List of host configurations to update.
        """
        hosts = hosts.copy()
        self.failed_hosts.clear()
        for host in hosts:
            ovh_client = OvhClient(host=host)
            if not ovh_client.update_ip(self.config.ip):
                self.failed_hosts.append(host)
        