from abc import ABC, abstractmethod
from typing import Any


class EventBus(ABC):
    @abstractmethod
    async def publish(self, event_name: str, payload: dict[str, Any]) -> None:
        """Publica un evento de dominio asíncronamente en el bus de eventos."""
        pass
