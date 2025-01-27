import ipify

from infrastructure.logger import Logger


class IpifyClient:
    def __init__(self):
        self.logger = Logger().get_logger()

    def get_public_ip(self) -> str:
        try:
            ip = ipify.get_ip()
            self.logger.info(f"Retrieved public IP: {ip}")
            return ip
        except Exception as e:
            self.logger.error(f"Failed to retrieve public IP: {e}")
            raise RuntimeError("Unable to fetch IP from ipify")