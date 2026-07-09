import uuid
from typing import Any
import httpx
from app.platform.config import settings


class TenantsGateway:
    def __init__(self, access_token: str) -> None:
        self._access_token = access_token

    async def get_tenant(self, tenant_id: uuid.UUID) -> dict[str, Any] | None:
        url = f"{settings.INTERNAL_API_BASE_URL.rstrip('/')}/tenants/{tenant_id}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url, headers=headers)
            except httpx.HTTPError:
                return None
        if response.status_code != 200:
            return None
        return response.json()
