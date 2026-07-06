import asyncio
import json
import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.domain.ports.bot_gateway import BotGateway

logger = logging.getLogger(__name__)


def _post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int = 20) -> None:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - destino configurado (n8n / callback propio)
        response.read()


class N8nBotGateway(BotGateway):
    """Adapter HTTP hacia el webhook del workflow de n8n.

    n8n recibe texto + contexto resumido y responde de forma asíncrona vía
    callback (`payload['callbackUrl']`). Nunca se le pasan credenciales de canal.

    Modo stub (`N8N_BOT_STUB=true`): en vez de llamar a n8n, hace eco al endpoint
    de callback real. Permite probar el loop completo end-to-end sin n8n ni Meta.
    """

    async def dispatch(self, payload: dict[str, Any]) -> None:
        if settings.N8N_BOT_STUB:
            await self._dispatch_stub(payload)
            return

        url = f"{settings.N8N_BASE_URL.rstrip('/')}{settings.N8N_INBOUND_WEBHOOK_PATH}"
        headers = {"Content-Type": "application/json"}
        if settings.N8N_API_KEY:
            headers["X-API-Key"] = settings.N8N_API_KEY

        try:
            await asyncio.to_thread(_post_json, url, headers, payload)
        except (HTTPError, URLError) as exc:
            logger.warning("No se pudo entregar el mensaje al bot n8n: %s", exc)
        except Exception as exc:  # noqa: BLE001 - no romper el flujo de inbound por el bot
            logger.exception("Error inesperado despachando a n8n: %s", exc)

    async def _dispatch_stub(self, payload: dict[str, Any]) -> None:
        """Eco local: ejercita el endpoint /bridge/n8n/reply real sin n8n."""
        await asyncio.sleep(0.1)
        reply = {
            "correlationId": payload["correlationId"],
            "tenantId": payload["business"]["tenantId"],
            "chatId": payload["conversation"]["chatId"],
            "customerId": payload["conversation"]["customerId"],
            "channel": payload["channel"],
            "reply": {
                "type": "TEXT",
                "content": f"[stub bot] Recibí: {payload['message']['content']}",
                "mediaUrl": None,
            },
            "memory": {"summary": None, "statePatch": {"stage": "stub_echo"}},
            "handoff": False,
        }
        url = payload.get("callbackUrl")
        if not url:
            logger.warning("Stub bot sin callbackUrl en el payload; no se puede cerrar el loop.")
            return
        headers = {"Content-Type": "application/json"}
        if settings.N8N_CALLBACK_SECRET:
            headers["X-Callback-Secret"] = settings.N8N_CALLBACK_SECRET
        try:
            await asyncio.to_thread(_post_json, url, headers, reply)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Stub bot no pudo llamar al callback: %s", exc)
