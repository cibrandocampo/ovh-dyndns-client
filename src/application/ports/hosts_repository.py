from abc import ABC, abstractmethod
from typing import List, Optional
from domain.hostconfig import HostConfig


class HostsRepository(ABC):
    @abstractmethod
    def get_hosts(self) -> List[HostConfig]:
        """Get the list of configured hosts."""
        pass

    @abstractmethod
    def get_pending_hosts(self) -> List[HostConfig]:
        """Get hosts that need updating (failed or never updated)."""
        pass

    @abstractmethod
    def get_host_by_hostname(self, hostname: str) -> Optional[HostConfig]:
        """Get a host by its hostname."""
        pass

    @abstractmethod
    def update_host_status(self, hostname: str, success: bool, error: str = None) -> None:
        """Update the status of a host after an update attempt."""
        pass
