from abc import ABC, abstractmethod
from typing import List
from domain.hostconfig import HostConfig


class HostsRepository(ABC):
    @abstractmethod
    def get_hosts(self) -> List[HostConfig]:
        """Obtiene la lista de hosts configurados."""
        pass
