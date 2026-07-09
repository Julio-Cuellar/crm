import uuid
from typing import Any

import httpx

from app.platform.config import settings


class CustomersFallbackGateway:
    """Fallback síncrono (Fase 1) para cuando `scheduling` necesita datos de un
    Customer recién creado que su proyección local aún no reflejó (lag de eventos).

    Llama al endpoint PÚBLICO de `customers` (nunca a su repositorio/DB interna),
    igual que lo haría un microservicio real. Marcado como PHASE1-SHIM: revisar una
    vez medida la latencia real de propagación de eventos en producción — ver plan
    de monolito modular.
    """

    def __init__(self, access_token: str) -> None:
        self._access_token = access_token

    async def get_customer(self, customer_id: uuid.UUID) -> dict[str, Any] | None:
        url = f"{settings.INTERNAL_API_BASE_URL.rstrip('/')}/customers/{customer_id}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url, headers=headers)
            except httpx.HTTPError:
                return None
        if response.status_code != 200:
            return None
        return response.json()
