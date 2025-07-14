from infrastructure.config import Config
from infrastructure.logger import Logger
from infrastructure.clients.ipify_client import IpifyClient
from infrastructure.clients.ovh_client import OvhClient

class UpdateDnsController:
    def __init__(self):
        self.ipify_client = IpifyClient()
        self.logger = Logger().get_logger()
        self.config = Config()

    def handler(self):
        self.logger.info("Starting DynDNS update process")
        
        try:
            ip = self.ipify_client.get_public_ip()
            if ip == self.config.ip:
                self.logger.info("IP has not changed since the last notification to providers")
            else:
                self.logger.info("New public IP, must be updated to providers")
                self.config.set_ip(new_ip=ip)

                for host in self.config.hosts_config:
                    ovh_client = OvhClient(host=host)
                    ovh_client.update_ip(ip)

        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            raise RuntimeError("DynDNS update failed")
