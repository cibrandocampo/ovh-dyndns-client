from abc import ABC, abstractmethod
from typing import Optional
from pydantic import IPvAnyAddress


class IpStateStore(ABC):
    @abstractmethod
    def get_ip(self) -> Optional[IPvAnyAddress]:
        """Obtiene la IP almacenada."""
        pass

    @abstractmethod
    def set_ip(self, ip: IPvAnyAddress) -> None:
        """Almacena la IP actual."""
        pass
