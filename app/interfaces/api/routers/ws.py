import uuid
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.infrastructure.db.repositories.sqlalchemy_blacklisted_token_repository import (
    SQLAlchemyBlacklistedTokenRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.websocket.manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


async def _authenticate(token: str, db: AsyncSession):
    """
    Valida el JWT recibido como query param.
    Los WebSocket del navegador no soportan headers custom, por eso usamos ?token=.
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None

    blacklist_repo = SQLAlchemyBlacklistedTokenRepository(db)
    if await blacklist_repo.is_blacklisted(token):
        return None

    user_repo = SQLAlchemyUserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        return None

    return user


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
        user = await _authenticate(token, db)

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
