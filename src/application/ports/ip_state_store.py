from abc import ABC, abstractmethod
from typing import Optional
from pydantic import IPvAnyAddress


class IpStateStore(ABC):
    @abstractmethod
    def get_ip(self) -> Optional[IPvAnyAddress]:
        """Get the stored IP address."""
        pass

    @abstractmethod
    def set_ip(self, ip: IPvAnyAddress) -> None:
        """Store the current IP address."""
        pass

    @abstractmethod
    def update_last_check(self) -> None:
        """Update the last check timestamp."""
        pass
