import uuid
from typing import Any

import httpx

from app.platform.config import settings


class CatalogFallbackGateway:
    """Fallback síncrono (Fase 1) para cuando `scheduling` necesita datos de un
    Service recién creado que su proyección local aún no reflejó. Ver docstring
    de `CustomersFallbackGateway` — mismo patrón y mismas advertencias (PHASE1-SHIM).
    """

    def __init__(self, access_token: str) -> None:
        self._access_token = access_token

    async def get_service(self, service_id: uuid.UUID) -> dict[str, Any] | None:
        url = f"{settings.INTERNAL_API_BASE_URL.rstrip('/')}/services/{service_id}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url, headers=headers)
            except httpx.HTTPError:
                return None
        if response.status_code != 200:
            return None
        return response.json()
