from datetime import datetime
from typing import Any, List
import httpx
from app.platform.config import settings


class SchedulingGateway:
    def __init__(self, access_token: str) -> None:
        self._access_token = access_token

    async def list_appointments(self, start_range: datetime, end_range: datetime) -> List[dict[str, Any]]:
        start_iso = start_range.isoformat()
        end_iso = end_range.isoformat()
        url = f"{settings.INTERNAL_API_BASE_URL.rstrip('/')}/appointments/"
        params = {
            "start_range": start_iso,
            "end_range": end_iso
        }
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
            except httpx.HTTPError:
                return []
        if response.status_code != 200:
            return []
        return response.json()
