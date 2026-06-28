import asyncio
import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings


@dataclass(slots=True)
class WhatsAppSendResult:
    message_id: str
    raw_response: dict[str, Any]


class WhatsAppCloudAPIError(Exception):
    def __init__(self, message: str, status_code: int = 502, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def _build_messages_url(phone_number_id: str) -> str:
    base_url = settings.META_GRAPH_API_BASE_URL.rstrip("/")
    version = settings.META_GRAPH_API_VERSION.strip("/")
    return f"{base_url}/{version}/{phone_number_id}/messages"


def _post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - request goes to configured Meta API
            response_body = response.read().decode("utf-8")
            if not response_body:
                return {}
            try:
                return json.loads(response_body)
            except json.JSONDecodeError:
                return {"raw": response_body}
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed_body = json.loads(error_body) if error_body else {}
        except json.JSONDecodeError:
            parsed_body = {"raw": error_body}

        error_message = parsed_body.get("error", {}).get(
            "message",
            f"WhatsApp API request failed with HTTP {exc.code}",
        )
        raise WhatsAppCloudAPIError(error_message, status_code=exc.code, details=parsed_body) from exc
    except URLError as exc:
        raise WhatsAppCloudAPIError(
            f"No se pudo conectar con WhatsApp Cloud API: {exc.reason}",
            status_code=502,
        ) from exc


async def send_whatsapp_message(
    *,
    phone_number_id: str,
    access_token: str,
    payload: dict[str, Any],
) -> WhatsAppSendResult:
    url = _build_messages_url(phone_number_id)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = await asyncio.to_thread(_post_json, url, headers, payload)
    message_id = ""

    messages = response.get("messages")
    if isinstance(messages, list) and messages:
        first_message = messages[0] or {}
        message_id = str(first_message.get("id") or "")

    if not message_id:
        message_id = str(response.get("message_id") or response.get("id") or "")

    return WhatsAppSendResult(message_id=message_id, raw_response=response)


async def send_whatsapp_text_message(
    *,
    phone_number_id: str,
    access_token: str,
    to: str,
    body: str,
) -> WhatsAppSendResult:
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {
            "body": body,
        },
    }
    return await send_whatsapp_message(
        phone_number_id=phone_number_id,
        access_token=access_token,
        payload=payload,
    )
