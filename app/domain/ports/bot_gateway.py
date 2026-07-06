from abc import ABC, abstractmethod
from typing import Any


class BotGateway(ABC):
    """Puerto de salida hacia el motor de bot (n8n).

    El backend solo entrega el mensaje actual + contexto resumido y recibe la
    respuesta por callback HTTP. El gateway NUNCA maneja credenciales del canal
    ni envía mensajes al cliente final: todo el I/O de canal vive en la capa de
    canal del backend (p. ej. `whatsapp_cloud_api`).

    Al ser un puerto, mañana su implementación puede cambiar de HTTP directo a
    un consumer de RabbitMQ sin tocar los routers ni los casos de uso.
    """

    @abstractmethod
    async def dispatch(self, payload: dict[str, Any]) -> None:
        """Envía el payload de conversación al workflow del bot de forma asíncrona."""
        pass
