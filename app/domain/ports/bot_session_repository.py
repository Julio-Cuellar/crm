import uuid
from abc import ABC, abstractmethod
from app.domain.entities.bot_session import BotSession


class BotSessionRepository(ABC):
    @abstractmethod
    async def save(self, session: BotSession) -> BotSession:
        pass

    @abstractmethod
    async def get_by_phone(self, phone: str) -> BotSession | None:
        pass

    @abstractmethod
    async def get_by_tenant_and_phone(self, tenant_id: uuid.UUID, phone: str) -> BotSession | None:
        pass

    @abstractmethod
    async def delete(self, phone: str) -> bool:
        pass
