import json
import logging
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Mantiene las conexiones WebSocket activas agrupadas por tenant_id.
    Singleton de módulo — se importa directamente donde se necesite.
    En producción multi-instancia reemplazar broadcast() por Redis Pub/Sub.
    """

    def __init__(self) -> None:
        self._connections: dict[UUID, list[WebSocket]] = {}

    async def connect(self, tenant_id: UUID, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(tenant_id, []).append(ws)
        logger.debug("WS conectado: tenant=%s total=%d", tenant_id, len(self._connections[tenant_id]))

    def disconnect(self, tenant_id: UUID, ws: WebSocket) -> None:
        conns = self._connections.get(tenant_id, [])
        if ws in conns:
            conns.remove(ws)
        logger.debug("WS desconectado: tenant=%s restantes=%d", tenant_id, len(conns))

    async def broadcast(self, tenant_id: UUID, event: dict) -> None:
        """Envía un evento JSON a todas las conexiones activas del tenant."""
        conns = self._connections.get(tenant_id, [])
        if not conns:
            return

        payload = json.dumps(event, default=str)
        dead: list[WebSocket] = []

        for ws in list(conns):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(tenant_id, ws)


# Singleton de módulo
ws_manager = WebSocketManager()
