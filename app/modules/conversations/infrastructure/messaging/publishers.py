import uuid
from typing import Any

from app.platform.messaging.event_bus import EventBus


async def publish_chat_inbound_simulated(
    event_bus: EventBus | None,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    chat_id: Any,
    content: str,
    message_type: str,
    media_url: str | None,
) -> None:
    """Dispara el procesamiento del bot para un mensaje entrante (hoy solo desde el
    simulador de desarrollo `/chats/{id}/incoming`). `conversations` no puede llamar a
    `DispatchToBotUseCase` directamente (vive en `assistant`, que sigue en app/legacy/ y
    los módulos no pueden importar de legacy) — en su lugar publica este evento, que
    `assistant` consume para reproducir exactamente el mismo dispatch."""
    if not event_bus:
        return
    payload = {
        "tenantId": str(tenant_id),
        "customerId": str(customer_id),
        "chatId": str(chat_id),
        "content": content,
        "messageType": message_type,
        "mediaUrl": media_url,
    }
    await event_bus.publish("chat.inbound_simulated", payload)
