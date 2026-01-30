import logging
from typing import List
from domain.hostconfig import HostConfig
from application.ports import IpProvider, DnsUpdater, IpStateStore, HostsRepository


class UpdateDnsController:
    def __init__(
        self,
        ip_provider: IpProvider,
        dns_updater: DnsUpdater,
        ip_state: IpStateStore,
        hosts_repo: HostsRepository,
        logger: logging.Logger
    ):
        self.ip_provider = ip_provider
        self.dns_updater = dns_updater
        self.ip_state = ip_state
        self.hosts_repo = hosts_repo
        self.logger = logger
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
            ip = self.ip_provider.get_public_ip()
            if ip == self.ip_state.get_ip():
                self.logger.info("IP unchanged, skipping update")
                if self.failed_hosts:
                    self.logger.info("Retrying failed hosts")
                    self.update_hosts_ip(self.failed_hosts, ip)
            else:
                self.logger.info("IP changed, updating hosts")
                self.ip_state.set_ip(ip)
                self.update_hosts_ip(self.hosts_repo.get_hosts(), ip)

        except Exception as e:
            self.logger.error(f"DNS update error: {e}")
            raise RuntimeError("DynDNS update failed")

    def update_hosts_ip(self, hosts: List[HostConfig], ip) -> None:
        """
        Updates the IP address for a list of hosts.

        Attempts to update each host's DNS record with the current IP.
        Failed updates are tracked in self.failed_hosts for retry.

        Args:
            hosts: List of host configurations to update.
            ip: The IP address to set.
        """
        hosts = hosts.copy()
        self.failed_hosts.clear()
        for host in hosts:
            if not self.dns_updater.update_ip(host, ip):
                self.failed_hosts.append(host)
