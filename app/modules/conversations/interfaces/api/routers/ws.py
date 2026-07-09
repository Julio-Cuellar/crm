import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.modules.identity.interfaces.api.dependencies.auth_bearer import get_user_from_raw_token
from app.platform.db.session import async_session_factory
from app.platform.websocket.manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/inbox")
async def inbox_ws(ws: WebSocket, token: str = Query(...)):
    """
    Canal WebSocket del Inbox.

    Eventos server → client:
      { type: "new_message",    customerId, customerName, preview, lastMessageAt }
      { type: "message_status", externalId, status }

    Eventos client → server:
      { type: "typing", customerId }
    """
    # Abrir sesión de DB manualmente (no podemos usar Depends en WebSocket fácilmente con async gen)
    async with async_session_factory() as db:
        user = await get_user_from_raw_token(token, db)

    if user is None:
        await ws.close(code=4001)
        return

    tenant_id = user.tenant_id
    await ws_manager.connect(tenant_id, ws)

    try:
        while True:
            data = await ws.receive_json()
            event_type = data.get("type")

            if event_type == "typing":
                # Rebroadcast a otros agentes del mismo tenant (excluye al emisor)
                await ws_manager.broadcast(tenant_id, {
                    "type": "agent_typing",
                    "customerId": data.get("customerId"),
                    "agentName": user.name,
                })

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning("WS error inesperado: %s", exc)
    finally:
        ws_manager.disconnect(tenant_id, ws)
