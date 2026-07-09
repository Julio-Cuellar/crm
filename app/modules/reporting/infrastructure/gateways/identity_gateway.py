from typing import Any, List
import httpx
from app.platform.config import settings


class IdentityGateway:
    def __init__(self, access_token: str) -> None:
        self._access_token = access_token

    async def list_users(self) -> List[dict[str, Any]]:
        url = f"{settings.INTERNAL_API_BASE_URL.rstrip('/')}/users/"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url, headers=headers)
            except httpx.HTTPError:
                return []
        if response.status_code != 200:
            return []
        return response.json()
