import uuid
from abc import ABC, abstractmethod

class ChatHistoryRepository(ABC):
    @abstractmethod
    async def get_or_create_chat(
        self, tenant_id: uuid.UUID, customer_id: uuid.UUID, platform: str = "WHATSAPP", external_thread_id: str | None = None
    ) -> dict:
        """Obtiene o crea un HistoryChat para el cliente y tenant especificados."""
        pass

    @abstractmethod
    async def list_chats_by_tenant(self, tenant_id: uuid.UUID) -> list[dict]:
        """Lista todos los HistoryChats activos para el tenant."""
        pass

    @abstractmethod
    async def get_messages_by_chat_id(self, chat_id: uuid.UUID) -> list[dict]:
        """Obtiene el historial ordenado de mensajes para una conversación."""
        pass

    @abstractmethod
    async def save_message(
        self,
        chat_id: uuid.UUID,
        direction: str,
        message_type: str,
        content: str,
        external_id: str | None = None,
        media_url: str | None = None,
        status: str = "SENT"
    ) -> dict:
        """Guarda un mensaje nuevo asociado a la conversación y actualiza la última interacción del chat."""
        pass

    @abstractmethod
    async def update_message_status_by_external_id(self, external_id: str, status: str) -> bool:
        """Actualiza el estado de un mensaje usando el id externo de WhatsApp."""
        pass
