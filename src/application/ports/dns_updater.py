from abc import ABC, abstractmethod
from typing import Tuple, Optional
from pydantic import IPvAnyAddress
from domain.hostconfig import HostConfig


class DnsUpdater(ABC):
    @abstractmethod
    def update_ip(self, host: HostConfig, ip: IPvAnyAddress) -> Tuple[bool, Optional[str]]:
        """
        Update the IP address of a host.

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
                - success: True if the update was successful
                - error_message: None if successful, error description if failed
        """
        pass
