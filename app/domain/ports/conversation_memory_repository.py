import uuid
from abc import ABC, abstractmethod
from typing import Any


class ConversationMemoryRepository(ABC):
    """Memoria compacta por conversación: resumen + estado estructurado + turnos.

    Sustituye el envío del historial plano a n8n. El resumen en lenguaje natural
    lo genera la IA (n8n) y aquí solo se persiste y se sirve. El estado es un JSON
    determinista del flujo (stage, cita pendiente, etc.). La clave es siempre el
    chat_id, que ya está aislado por tenant -> imposible mezclar negocios.
    """

    @abstractmethod
    async def get(self, chat_id: uuid.UUID) -> dict[str, Any]:
        """Devuelve {'summary': {...}, 'state': {...}, 'turns': int} de la conversación."""
        pass

    @abstractmethod
    async def bump_turn(self, chat_id: uuid.UUID) -> int:
        """Incrementa el contador de turnos del chat y devuelve el nuevo valor."""
        pass

    @abstractmethod
    async def save_summary(self, chat_id: uuid.UUID, text: str, version: int) -> None:
        """Guarda el resumen recompactado por la IA y reinicia turnsSinceRefresh."""
        pass

    @abstractmethod
    async def merge_state(self, chat_id: uuid.UUID, patch: dict[str, Any]) -> None:
        """Aplica un patch parcial sobre el estado estructurado del flujo."""
        pass

    @abstractmethod
    async def mark_processed(self, correlation_id: str) -> bool:
        """Marca un correlationId como procesado.

        Devuelve True si es la primera vez (procesar), False si ya existía
        (respuesta duplicada -> ignorar). Garantiza idempotencia del callback.
        """
        pass
