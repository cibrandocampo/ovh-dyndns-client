from abc import ABC, abstractmethod
from pydantic import IPvAnyAddress
from domain.hostconfig import HostConfig


class DnsUpdater(ABC):
    @abstractmethod
    def update_ip(self, host: HostConfig, ip: IPvAnyAddress) -> bool:
        """Actualiza la IP de un host. Retorna True si tuvo éxito."""
        pass
