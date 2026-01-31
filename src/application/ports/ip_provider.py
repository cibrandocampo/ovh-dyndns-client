from abc import ABC, abstractmethod
from pydantic import IPvAnyAddress


class IpProvider(ABC):
    @abstractmethod
    def get_public_ip(self) -> IPvAnyAddress:
        """Get the current public IP address."""
        pass
