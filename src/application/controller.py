import logging
from typing import List, Tuple
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
            self.ip_state.update_last_check()

            if ip == self.ip_state.get_ip():
                self.logger.info("IP unchanged")
                pending_hosts = self.hosts_repo.get_pending_hosts()
                if pending_hosts:
                    self.logger.info(f"Updating {len(pending_hosts)} pending hosts")
                    self.update_hosts_ip(pending_hosts, ip)
                else:
                    self.logger.info("All hosts up to date")
            else:
                self.logger.info("IP changed, updating all hosts")
                self.ip_state.set_ip(ip)
                self.update_hosts_ip(self.hosts_repo.get_hosts(), ip)

        except Exception as e:
            self.logger.error(f"DNS update error: {e}")
            raise RuntimeError("DynDNS update failed")

    def update_hosts_ip(self, hosts: List[HostConfig], ip) -> None:
        """
        Updates the IP address for a list of hosts.

        Attempts to update each host's DNS record with the current IP.
        Status is persisted in the database for retry on next cycle.

        Args:
            hosts: List of host configurations to update.
            ip: The IP address to set.
        """
        for host in hosts:
            try:
                success, error_message = self.dns_updater.update_ip(host, ip)
                self.hosts_repo.update_host_status(
                    hostname=host.hostname,
                    success=success,
                    error=error_message
                )
                if success:
                    self.logger.info(f"{host.hostname} | Update successful")
                else:
                    self.logger.warning(f"{host.hostname} | Update failed: {error_message}")
            except Exception as e:
                self.logger.error(f"Error updating {host.hostname}: {e}")
                self.hosts_repo.update_host_status(
                    hostname=host.hostname,
                    success=False,
                    error=str(e)
                )

    def force_update_host(self, hostname: str) -> Tuple[bool, str]:
        """
        Force update a specific host's DNS record.

        Args:
            hostname: The hostname to update.

        Returns:
            Tuple[bool, str]: (success, message)
        """
        self.logger.info(f"Force updating host: {hostname}")

        host = self.hosts_repo.get_host_by_hostname(hostname)
        if not host:
            return False, f"Host {hostname} not found"

        try:
            ip = self.ip_state.get_ip()
            if not ip:
                ip = self.ip_provider.get_public_ip()
                self.ip_state.set_ip(ip)

            self.ip_state.update_last_check()

            success, error_message = self.dns_updater.update_ip(host, ip)
            self.hosts_repo.update_host_status(hostname, success, error_message)

            if success:
                return True, f"Host {hostname} updated successfully"
            else:
                return False, error_message or "Unknown error"

        except Exception as e:
            self.logger.error(f"Error force updating {hostname}: {e}")
            self.hosts_repo.update_host_status(hostname, False, str(e))
            return False, str(e)
